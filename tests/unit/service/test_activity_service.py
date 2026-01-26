from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from freezegun import freeze_time

from app.exceptions.business import (
    BusinessRuleViolationError,
    DatabaseError,
    EntityNotFoundError,
)
from app.models.activity import Activity
from app.models.program import Program
from app.models.user import User
from app.repositories.achievement_repository import AchievementRepository
from app.repositories.activity_repository import ActivityRepository
from app.schemas.activity_schema import ActivityCreate, ActivityUpdate
from app.services.activity_service import ActivityService
from app.services.program_service import ProgramService
from app.services.user_service import UserService


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def mock_user_service():
    return AsyncMock(spec=UserService)


@pytest.fixture
def mock_program_service():
    return AsyncMock(spec=ProgramService)


@pytest.fixture
def mock_activity_repo():
    return AsyncMock(spec=ActivityRepository)


@pytest.fixture
def mock_achievement_repo():
    return AsyncMock(spec=AchievementRepository)


@pytest.fixture
def activity_service(
    mock_db,
    mock_user_service,
    mock_program_service,
    mock_activity_repo,
    mock_achievement_repo,
):
    return ActivityService(
        db=mock_db,
        user_service=mock_user_service,
        program_service=mock_program_service,
        activity_repo=mock_activity_repo,
        achievement_repo=mock_achievement_repo,
    )


@pytest.fixture
def today():
    return datetime.now()


@pytest.fixture
def user():
    return User(id=1, slack_id="U123", display_name="Test User")


@pytest.fixture
def program(today):
    return Program(
        id=1,
        name="Test Program",
        slack_channel="C123",
        start_date=datetime(today.year, 1, 1),
        end_date=datetime(today.year + 1, 1, 1),
    )


@pytest.fixture
def setup_mocks(
    activity_service,
    mock_user_service,
    mock_program_service,
    mock_activity_repo,
    mock_achievement_repo,
    user,
    program,
):
    mock_user_service.find_by_slack_id.return_value = user
    mock_program_service.find_by_slack_channel.return_value = [program]
    mock_program_service.find_by_id.return_value = program
    mock_program_service.find_by_name.return_value = program

    mock_activity_repo.check_activity_same_day.return_value = None
    mock_activity_repo.count_monthly.return_value = 5
    mock_achievement_repo.user_has_achievement.return_value = False

    mock_activity_repo.create.side_effect = lambda act: setattr(
        act, "id", 1
    )
    return {"user": user, "program": program}


async def _assert_error(coroutine, expected_error, match=None):
    with pytest.raises(expected_error) as exc:
        await coroutine
    if match:
        assert match in str(exc.value)


@pytest.mark.anyio
class TestActivityCreate:
    async def test_create_activity_success(
        self, activity_service, setup_mocks, today, mock_activity_repo
    ):
        activity_create = ActivityCreate(
            description="Run", performed_at=today, evidence_url="https://evidence.com"
        )
        result = await activity_service.create(activity_create, "C123", "U123")

        assert result.count_month == 5
        mock_activity_repo.create.assert_called_once()
        mock_activity_repo.count_monthly.assert_called_once()

    async def test_create_activity_auto_create_user(
        self, activity_service, mock_user_service, setup_mocks, today
    ):
        mock_user_service.find_by_slack_id.return_value = None
        mock_user_service.get_slack_display_name.return_value = "New User"
        mock_user_service.create.return_value = User(
            id=99, slack_id="U_NEW", display_name="New User"
        )

        await activity_service.create(
            ActivityCreate(description="Run",
                           performed_at=today), "C123", "U_NEW"
        )
        mock_user_service.create.assert_called_once()

    @pytest.mark.parametrize(
        "find_programs_return, expected_error, match",
        [
            ([], EntityNotFoundError, "Program"),
            (
                [Program(id=1), Program(id=2)],
                BusinessRuleViolationError,
                "not possible to determine",
            ),
        ],
    )
    async def test_create_fails_on_program_resolution(
        self,
        activity_service,
        mock_program_service,
        setup_mocks,
        today,
        find_programs_return,
        expected_error,
        match,
    ):
        mock_program_service.find_by_slack_channel.return_value = find_programs_return
        await _assert_error(
            activity_service.create(
                ActivityCreate(description="R", performed_at=today), "C", "U"
            ),
            expected_error,
            match,
        )

    async def test_create_fails_when_activity_already_exists(
        self, activity_service, setup_mocks, today, mock_activity_repo
    ):
        mock_activity_repo.check_activity_same_day.return_value = Activity(
            id=99
        )
        await _assert_error(
            activity_service.create(
                ActivityCreate(description="R", performed_at=today), "C", "U"
            ),
            BusinessRuleViolationError,
            "already registered",
        )

    @pytest.mark.parametrize(
        "delta, match",
        [
            (timedelta(hours=1), "future"),
            (timedelta(days=-400), "current or previous month"),
        ],
    )
    async def test_create_fails_on_date_validation(
        self, activity_service, setup_mocks, today, delta, match
    ):
        invalid_date = today + delta

        async def call_create():
            activity_create = ActivityCreate(
                description="R", performed_at=invalid_date)
            await activity_service.create(activity_create, "C", "U")

        await _assert_error(
            call_create(),
            BusinessRuleViolationError,
            match,
        )

    async def test_create_fails_on_database_error(
        self, activity_service, setup_mocks, today, mock_activity_repo
    ):
        mock_activity_repo.create.side_effect = Exception("DB Fail")
        await _assert_error(
            activity_service.create(
                ActivityCreate(description="R", performed_at=today), "C", "U"
            ),
            DatabaseError,
        )


@pytest.mark.anyio
class TestActivityUpdate:
    async def test_update_activity_success(
        self, activity_service, setup_mocks, today, mock_activity_repo
    ):
        existing = Activity(id=1, program_id=1, performed_at=today, user_id=1)
        mock_activity_repo.find_by_id_and_slack_id.return_value = existing

        result = await activity_service.update(
            ActivityUpdate(description="Up"), 1, "U123"
        )

        assert result.id == 1
        activity_service.db.commit.assert_called_once()

    @pytest.mark.parametrize(
        "mock_target, mock_value, expected_error, match",
        [
            ("mock_user_service.find_by_slack_id",
             None, EntityNotFoundError, "User"),
            (
                "mock_activity_repo.find_by_id_and_slack_id",
                None,
                EntityNotFoundError,
                "Activity",
            ),
            ("mock_program_service.find_by_id",
             None, EntityNotFoundError, "Program"),
        ],
    )
    async def test_update_fails_on_entity_not_found(
        self,
        activity_service,
        mock_user_service,
        mock_program_service,
        mock_activity_repo,
        setup_mocks,
        mock_target,
        mock_value,
        expected_error,
        match,
    ):
        if "activity_repo" in mock_target:
            mock_activity_repo.find_by_id_and_slack_id.return_value = (
                mock_value
            )
        else:
            obj_name, method_name = mock_target.split(".")
            getattr(locals()[obj_name], method_name).return_value = mock_value

        await _assert_error(
            activity_service.update(ActivityUpdate(description="Up"), 1, "U"),
            expected_error,
            match,
        )

    async def test_update_fails_when_date_conflict(
        self, activity_service, setup_mocks, today, mock_activity_repo
    ):
        mock_activity_repo.find_by_id_and_slack_id.return_value = Activity(
            id=1, program_id=1, performed_at=today - timedelta(days=1), user_id=1
        )
        mock_activity_repo.check_activity_same_day.return_value = Activity(
            id=99
        )

        await _assert_error(
            activity_service.update(
                ActivityUpdate(performed_at=today), 1, "U"),
            BusinessRuleViolationError,
            "already registered",
        )


@pytest.mark.anyio
class TestActivityDelete:
    async def test_delete_activity_success(
        self, activity_service, setup_mocks, today, mock_activity_repo
    ):
        existing = Activity(id=1, performed_at=today, user_id=1)
        mock_activity_repo.find_by_id_and_slack_id.return_value = existing

        await activity_service.delete(1, "U123")

        activity_service.db.delete.assert_called_once_with(existing)
        activity_service.db.commit.assert_called_once()

    @pytest.mark.parametrize(
        "performed_at, expected_error, match",
        [
            (None, EntityNotFoundError, "Activity"),
            (
                datetime(2020, 1, 1),
                BusinessRuleViolationError,
                "current or previous month",
            ),
        ],
    )
    async def test_delete_fails_on_validation(
        self,
        activity_service,
        setup_mocks,
        performed_at,
        expected_error,
        match,
        mock_activity_repo,
    ):
        mock_activity_repo.find_by_id_and_slack_id.return_value = (
            Activity(id=1, performed_at=performed_at) if performed_at else None
        )
        await _assert_error(activity_service.delete(1, "U"), expected_error, match)


@pytest.mark.anyio
class TestActivityQuery:
    async def test_query_methods_success(
        self, activity_service, setup_mocks, mock_activity_repo
    ):
        repo = mock_activity_repo
        repo.find_by_user_id_and_date.return_value = [Activity(id=1)]
        repo.find_by_user_id_and_slack_channel_and_date.return_value = [
            Activity(id=2)]
        repo.find_users_with_completed_program.return_value = [1]
        repo.find_by_id_and_slack_id.return_value = Activity(id=3)

        assert (await activity_service.find_by_user("U", "2023-10"))[0].id == 1
        assert (await activity_service.find_by_user_and_program("C", "U", "2023-10"))[
            0
        ].id == 2
        assert (
            await activity_service.find_all_user_by_program_completed("P", "2023-10")
        ) == [1]
        assert (await activity_service.find_by_id(1, "U")).id == 3

    @pytest.mark.parametrize(
        "method, args, mock_target, expected_error, match",
        [
            (
                "find_by_id",
                (1, "U"),
                "activity_repo.find_by_id_and_slack_id",
                EntityNotFoundError,
                "Activity",
            ),
            (
                "find_by_user",
                ("U", "2023-10"),
                "user_service.find_by_slack_id",
                EntityNotFoundError,
                "User",
            ),
            (
                "find_by_user_and_program",
                ("C", "U", "2023-10"),
                "user_service.find_by_slack_id",
                EntityNotFoundError,
                "User",
            ),
            (
                "find_all_user_by_program_completed",
                ("P", "2023-10"),
                "program_service.find_by_name",
                EntityNotFoundError,
                "Program",
            ),
        ],
    )
    async def test_query_fails_when_not_found(
        self,
        activity_service,
        setup_mocks,
        mock_activity_repo,
        method,
        args,
        mock_target,
        expected_error,
        match,
    ):
        if "activity_repo" in mock_target:
            mock_activity_repo.find_by_id_and_slack_id.return_value = None
        elif "user_service" in mock_target:
            activity_service.user_service.find_by_slack_id.return_value = None
        else:
            activity_service.program_service.find_by_name.return_value = None

        await _assert_error(
            getattr(activity_service, method)(*args), expected_error, match
        )


@pytest.mark.anyio
class TestActivityTimezone:
    @pytest.mark.parametrize("tz_offset", [0, -3, 5])
    async def test_timezone_handling(
        self, activity_service, setup_mocks, today, tz_offset, mock_activity_repo
    ):
        tz = timezone(timedelta(hours=tz_offset))
        performed_at = today.replace(tzinfo=tz)

        # Mock program with same timezone
        setup_mocks["program"].start_date = (today - timedelta(days=10)).replace(
            tzinfo=tz
        )
        setup_mocks["program"].end_date = (today + timedelta(days=10)).replace(
            tzinfo=tz
        )

        await activity_service.create(
            ActivityCreate(description="R",
                           performed_at=performed_at), "C", "U"
        )
        created = mock_activity_repo.create.call_args[0][0]
        assert created.performed_at.tzinfo == tz


@pytest.mark.anyio
class TestCreateRetroactiveAchievement:
    async def test_create_activity_triggers_retro_achievement_when_12_prev_month(
        self,
        activity_service,
        mock_user_service,
        mock_program_service,
        mock_activity_repo,
        mock_achievement_repo,
        user,
    ):
        with freeze_time("2026-01-20"):
            program_2025 = Program(
                id=1,
                slack_channel="C123",
                start_date=datetime(2025, 1, 1),
                end_date=datetime(2026, 12, 31),
            )

            # Setup mocks
            mock_user_service.find_by_slack_id.return_value = user
            mock_program_service.find_by_slack_channel.return_value = [
                program_2025]
            mock_activity_repo.check_activity_same_day.return_value = None
            mock_activity_repo.count_monthly.return_value = 12
            mock_achievement_repo.user_has_achievement.return_value = False

            async def assign_id(activity):
                activity.id = 1

            mock_activity_repo.create.side_effect = assign_id

            previous_month_date = datetime(2025, 12, 15)

            activity_create = ActivityCreate(
                description="12ª Activity",
                performed_at=previous_month_date,
                evidence_url="http://test.com",
            )

            result = await activity_service.create(activity_create, "C123", "U123")

            assert result.count_month == 12

            mock_achievement_repo.create.assert_called_once()

            call_args = mock_achievement_repo.create.call_args
            achievement = call_args[0][0]  # First positional argument
            assert achievement.user_id == 1
            assert achievement.program_id == 1
            assert achievement.cycle_reference == "2025-12"

    async def test_create_activity_does_not_trigger_achievement_when_only_11_activities(
        self,
        activity_service,
        mock_user_service,
        mock_program_service,
        mock_activity_repo,
        mock_achievement_repo,
        user,
    ):
        with freeze_time("2026-01-20"):
            program_2025 = Program(
                id=1,
                slack_channel="C123",
                start_date=datetime(2025, 1, 1),
                end_date=datetime(2026, 12, 31),
            )

            mock_user_service.find_by_slack_id.return_value = user
            mock_program_service.find_by_slack_channel.return_value = [
                program_2025]
            mock_activity_repo.check_activity_same_day.return_value = None
            mock_activity_repo.count_monthly.return_value = 11

            async def assign_id(activity):
                activity.id = 1

            mock_activity_repo.create.side_effect = assign_id

            previous_month_date = datetime(2025, 12, 15)

            activity_create = ActivityCreate(
                description="11ª Activity",
                performed_at=previous_month_date,
                evidence_url="http://test.com",
            )

            await activity_service.create(activity_create, "C123", "U123")

            mock_achievement_repo.create.assert_not_called()

    async def test_create_activity_does_not_trigger_achievement_when_current_month(
        self,
        activity_service,
        mock_user_service,
        mock_program_service,
        mock_activity_repo,
        mock_achievement_repo,
        user,
    ):
        with freeze_time("2026-01-20"):
            program_2026 = Program(
                id=1,
                slack_channel="C123",
                start_date=datetime(2026, 1, 1),
                end_date=datetime(2026, 12, 31),
            )

            mock_user_service.find_by_slack_id.return_value = user
            mock_program_service.find_by_slack_channel.return_value = [
                program_2026]
            mock_activity_repo.check_activity_same_day.return_value = None
            mock_activity_repo.count_monthly.return_value = 12

            async def assign_id(activity):
                activity.id = 1

            mock_activity_repo.create.side_effect = assign_id

            current_month_date = datetime(2026, 1, 15)

            activity_create = ActivityCreate(
                description="Activity",
                performed_at=current_month_date,
                evidence_url="http://test.com",
            )

            await activity_service.create(activity_create, "C123", "U123")

            mock_achievement_repo.create.assert_not_called()

    async def test_create_activity_does_not_duplicate_achievement_when_already_exists(
        self,
        activity_service,
        mock_user_service,
        mock_program_service,
        mock_activity_repo,
        mock_achievement_repo,
        user,
    ):
        with freeze_time("2026-01-20"):
            program_2025 = Program(
                id=1,
                slack_channel="C123",
                start_date=datetime(2025, 1, 1),
                end_date=datetime(2026, 12, 31),
            )

            mock_user_service.find_by_slack_id.return_value = user
            mock_program_service.find_by_slack_channel.return_value = [
                program_2025]
            mock_activity_repo.check_activity_same_day.return_value = None
            mock_activity_repo.count_monthly.return_value = 12
            mock_achievement_repo.user_has_achievement.return_value = True

            async def assign_id(activity):
                activity.id = 1

            mock_activity_repo.create.side_effect = assign_id

            previous_month_date = datetime(2025, 12, 15)

            activity_create = ActivityCreate(
                description="12ª Activity",
                performed_at=previous_month_date,
                evidence_url="http://test.com",
            )

            result = await activity_service.create(activity_create, "C123", "U123")

            assert result.count_month == 12
            mock_achievement_repo.user_has_achievement.assert_called_once()
            mock_achievement_repo.create.assert_not_called()

    async def test_create_activity_succeeds_even_when_achievement_creation_fails(
        self,
        activity_service,
        mock_user_service,
        mock_program_service,
        mock_activity_repo,
        mock_achievement_repo,
        user,
    ):
        with freeze_time("2026-01-20"):
            program_2025 = Program(
                id=1,
                name="Test Program",
                slack_channel="C123",
                start_date=datetime(2025, 1, 1),
                end_date=datetime(2026, 12, 31),
            )

            mock_user_service.find_by_slack_id.return_value = user
            mock_program_service.find_by_slack_channel.return_value = [
                program_2025]
            mock_activity_repo.check_activity_same_day.return_value = None
            mock_activity_repo.count_monthly.return_value = 12
            mock_achievement_repo.user_has_achievement.return_value = False
            mock_achievement_repo.create.side_effect = Exception("DB Error")

            async def assign_id(activity):
                activity.id = 1

            mock_activity_repo.create.side_effect = assign_id

            previous_month_date = datetime(2025, 12, 15)

            activity_create = ActivityCreate(
                description="12ª Activity",
                performed_at=previous_month_date,
                evidence_url="http://test.com",
            )

            # Should not raise exception, activity creation should succeed
            result = await activity_service.create(activity_create, "C123", "U123")

            assert result.count_month == 12
            assert result.id == 1
