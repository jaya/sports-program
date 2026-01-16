from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from app.exceptions.business import (
    BusinessRuleViolationError,
    DatabaseError,
    EntityNotFoundError,
)
from app.models.activity import Activity
from app.models.program import Program
from app.models.user import User
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
def activity_service(mock_db, mock_user_service, mock_program_service):
    service = ActivityService(
        db=mock_db, user_service=mock_user_service, program_service=mock_program_service
    )
    service.activity_repo = AsyncMock(spec=ActivityRepository)
    return service


@pytest.fixture
def today():
    return datetime.now()


@pytest.fixture
def user():
    return User(id=1, slack_id="U123")


@pytest.fixture
def program(today):
    return Program(
        id=1,
        slack_channel="C123",
        start_date=datetime(today.year, 1, 1),
        end_date=datetime(today.year + 1, 1, 1),
    )


@pytest.fixture
def setup_mocks(
    activity_service, mock_user_service, mock_program_service, user, program
):
    mock_user_service.find_by_slack_id.return_value = user
    mock_program_service.find_by_slack_channel.return_value = [program]
    mock_program_service.find_by_id.return_value = program

    activity_service.activity_repo.check_activity_same_day.return_value = None
    activity_service.activity_repo.count_monthly.return_value = 5

    async def assign_id(activity):
        activity.id = 1

    activity_service.activity_repo.create.side_effect = assign_id


async def _assert_error(coroutine, expected_error, match=None):
    with pytest.raises(expected_error) as exc:
        await coroutine
    if match:
        assert match in str(exc.value)


def _mock_setup_defaults(
    mock_user_service, mock_program_service, activity_service, today
):
    mock_user_service.find_by_slack_id.return_value = User(id=1)
    program = Program(
        id=1,
        start_date=datetime(today.year, 1, 1),
        end_date=datetime(today.year, 12, 31),
    )
    mock_program_service.find_by_slack_channel.return_value = [program]
    mock_program_service.find_by_id.return_value = program

    activity_service.activity_repo.check_activity_same_day.return_value = None
    activity_service.activity_repo.create.side_effect = lambda act: setattr(
        act, "id", 1
    )
    activity_service.activity_repo.count_monthly.return_value = 1

    return program


def _mock_activity_exists(activity_service):
    activity_service.activity_repo.check_activity_same_day.return_value = Activity(
        id=99
    )


def _mock_activity_in_repo(activity_service, performed_at=None, program_id=1):
    act = Activity(
        id=1,
        program_id=program_id,
        performed_at=performed_at or datetime.now(),
        user_id=1,
    )
    activity_service.activity_repo.find_by_id_and_slack_id.return_value = act
    return act


@pytest.mark.anyio
async def test_create_activity_success(activity_service, setup_mocks, today):
    activity_create = ActivityCreate(
        description="Run", performed_at=today, evidence_url="http://evidence.com"
    )
    result = await activity_service.create(activity_create, "C123", "U123")

    assert result.count_month == 5
    activity_service.activity_repo.create.assert_called_once()
    activity_service.activity_repo.count_monthly.assert_called_once()


@pytest.mark.anyio
async def test_update_activity_success(activity_service, setup_mocks, today):
    existing = Activity(id=1, program_id=1, performed_at=today, user_id=1)
    activity_service.activity_repo.find_by_id_and_slack_id.return_value = existing

    result = await activity_service.update(ActivityUpdate(description="Up"), 1, "U123")

    assert result.id == 1
    activity_service.db.commit.assert_called_once()


@pytest.mark.anyio
async def test_delete_activity_success(activity_service, setup_mocks, today):
    existing = Activity(id=1, performed_at=today, user_id=1)
    activity_service.activity_repo.find_by_id_and_slack_id.return_value = existing

    await activity_service.delete(1, "U123")

    activity_service.db.delete.assert_called_once_with(existing)
    activity_service.db.commit.assert_called_once()


@pytest.mark.anyio
async def test_create_fails_when_activity_already_exists(
    activity_service, mock_user_service, mock_program_service, setup_mocks, today
):
    _mock_setup_defaults(
        mock_user_service, mock_program_service, activity_service, today
    )
    _mock_activity_exists(activity_service)

    await _assert_error(
        activity_service.create(
            ActivityCreate(description="R", performed_at=today), "C", "U"
        ),
        BusinessRuleViolationError,
        "already registered",
    )


@pytest.mark.anyio
async def test_create_fails_when_program_not_found(
    activity_service, mock_user_service, mock_program_service, setup_mocks, today
):
    _mock_setup_defaults(
        mock_user_service, mock_program_service, activity_service, today
    )
    mock_program_service.find_by_slack_channel.return_value = []

    await _assert_error(
        activity_service.create(
            ActivityCreate(description="R", performed_at=today), "C", "U"
        ),
        EntityNotFoundError,
        "Program",
    )


@pytest.mark.anyio
async def test_create_fails_when_multiple_programs_ambiguous(
    activity_service, mock_user_service, mock_program_service, setup_mocks, today
):
    _mock_setup_defaults(
        mock_user_service, mock_program_service, activity_service, today
    )
    mock_program_service.find_by_slack_channel.return_value = [
        Program(id=1),
        Program(id=2),
    ]

    await _assert_error(
        activity_service.create(
            ActivityCreate(description="R", performed_at=today), "C", "U"
        ),
        BusinessRuleViolationError,
        "not possible to determine",
    )


@pytest.mark.anyio
async def test_create_fails_on_database_error(
    activity_service, mock_user_service, mock_program_service, setup_mocks, today
):
    _mock_setup_defaults(
        mock_user_service, mock_program_service, activity_service, today
    )
    activity_service.activity_repo.create.side_effect = Exception("DB Fail")

    await _assert_error(
        activity_service.create(
            ActivityCreate(description="R", performed_at=today), "C", "U"
        ),
        DatabaseError,
    )


@pytest.mark.anyio
async def test_create_fails_when_date_in_future(
    activity_service, mock_user_service, mock_program_service, setup_mocks, today
):
    _mock_setup_defaults(
        mock_user_service, mock_program_service, activity_service, today
    )
    future = datetime.now() + timedelta(hours=1)

    await _assert_error(
        activity_service.create(
            ActivityCreate(description="R", performed_at=future), "C", "U"
        ),
        BusinessRuleViolationError,
        "future",
    )


@pytest.mark.anyio
async def test_create_activity_auto_create_user(
    activity_service,
    mock_user_service,
    mock_program_service,
    today,
    program,
    setup_mocks,
):
    _mock_setup_defaults(
        mock_user_service, mock_program_service, activity_service, today
    )
    mock_user_service.find_by_slack_id.return_value = None
    mock_user_service.create.return_value = User(id=99, slack_id="U_NEW")

    await activity_service.create(
        ActivityCreate(description="Run", performed_at=today), "C123", "U_NEW"
    )
    mock_user_service.create.assert_called_once()


@pytest.mark.anyio
async def test_update_fails_when_user_missing(
    activity_service, mock_user_service, mock_program_service, setup_mocks
):
    mock_user_service.find_by_slack_id.return_value = None
    await _assert_error(
        activity_service.update(ActivityUpdate(performed_at=datetime.now()), 1, "U"),
        EntityNotFoundError,
        "User",
    )


@pytest.mark.anyio
async def test_update_fails_when_activity_missing(
    activity_service, mock_user_service, mock_program_service, setup_mocks
):
    mock_user_service.find_by_slack_id.return_value = User(id=1)
    activity_service.activity_repo.find_by_id_and_slack_id.return_value = None
    await _assert_error(
        activity_service.update(ActivityUpdate(performed_at=datetime.now()), 1, "U"),
        EntityNotFoundError,
        "Activity",
    )


@pytest.mark.anyio
async def test_update_fails_when_program_missing(
    activity_service, mock_user_service, mock_program_service, setup_mocks
):
    mock_user_service.find_by_slack_id.return_value = User(id=1)
    _mock_activity_in_repo(activity_service)
    mock_program_service.find_by_id.return_value = None

    await _assert_error(
        activity_service.update(ActivityUpdate(performed_at=datetime.now()), 1, "U"),
        EntityNotFoundError,
        "Program",
    )


@pytest.mark.anyio
async def test_update_fails_when_date_conflict(
    activity_service, mock_user_service, mock_program_service, setup_mocks, today
):
    _mock_setup_defaults(
        mock_user_service, mock_program_service, activity_service, today
    )
    _mock_activity_in_repo(activity_service, performed_at=today - timedelta(days=1))
    _mock_activity_exists(activity_service)

    await _assert_error(
        activity_service.update(ActivityUpdate(performed_at=today), 1, "U"),
        BusinessRuleViolationError,
        "already registered",
    )


@pytest.mark.anyio
async def test_update_fails_on_database_error(
    activity_service, mock_user_service, mock_program_service, setup_mocks, today
):
    _mock_setup_defaults(
        mock_user_service, mock_program_service, activity_service, today
    )
    _mock_activity_in_repo(activity_service)
    activity_service.db.commit.side_effect = Exception("DB")

    await _assert_error(
        activity_service.update(ActivityUpdate(performed_at=today), 1, "U"),
        DatabaseError,
    )


@pytest.mark.anyio
async def test_update_activity_date_success_no_conflict(
    activity_service, setup_mocks, today
):
    yesterday = today - timedelta(days=1)
    current_activity = Activity(id=1, program_id=1, performed_at=yesterday, user_id=1)
    activity_service.activity_repo.find_by_id_and_slack_id.return_value = (
        current_activity
    )
    activity_service.activity_repo.check_activity_same_day.return_value = None

    activity_service.user_service.find_by_slack_id.return_value = User(id=1)
    activity_service.program_service.find_by_id.return_value = Program(
        id=1, start_date=yesterday
    )

    result = await activity_service.update(
        ActivityUpdate(performed_at=today), 1, "U123"
    )
    assert result.id == 1


@pytest.mark.anyio
async def test_delete_fails_when_activity_not_found(activity_service, setup_mocks):
    activity_service.activity_repo.find_by_id_and_slack_id.return_value = None
    await _assert_error(
        activity_service.delete(1, "U"), EntityNotFoundError, "Activity"
    )


@pytest.mark.anyio
async def test_delete_fails_when_outside_allowed_window(activity_service, setup_mocks):
    activity_service.activity_repo.find_by_id_and_slack_id.return_value = Activity(
        id=1, performed_at=datetime(2020, 1, 1)
    )
    await _assert_error(
        activity_service.delete(1, "U"),
        BusinessRuleViolationError,
        "current or previous month",
    )


@pytest.mark.anyio
async def test_delete_fails_on_database_error(activity_service, setup_mocks):
    activity_service.activity_repo.find_by_id_and_slack_id.return_value = Activity(
        id=1, performed_at=datetime.now()
    )
    activity_service.db.delete.side_effect = Exception("Fail")
    await _assert_error(activity_service.delete(1, "U"), DatabaseError)


@pytest.mark.anyio
async def test_find_by_id_fails_when_not_found(activity_service, setup_mocks):
    activity_service.activity_repo.find_by_id_and_slack_id.return_value = None
    await _assert_error(
        activity_service.find_by_id(1, "U"), EntityNotFoundError, "Activity"
    )


@pytest.mark.anyio
async def test_find_by_user_fails_when_user_not_found(
    activity_service, mock_user_service, setup_mocks
):
    mock_user_service.find_by_slack_id.return_value = None
    await _assert_error(
        activity_service.find_by_user("U", "2023-10"), EntityNotFoundError, "User"
    )


@pytest.mark.anyio
async def test_find_by_user_program_fails_when_user_not_found(
    activity_service, mock_user_service, setup_mocks
):
    mock_user_service.find_by_slack_id.return_value = None
    await _assert_error(
        activity_service.find_by_user_and_program("C", "U", "2023-10"),
        EntityNotFoundError,
        "User",
    )


@pytest.mark.anyio
async def test_find_all_fails_when_program_not_found(
    activity_service, mock_program_service, setup_mocks
):
    mock_program_service.find_by_name.return_value = None
    await _assert_error(
        activity_service.find_all_user_by_program_completed("P", "2023-10"),
        EntityNotFoundError,
        "Program",
    )


@pytest.mark.anyio
async def test_find_success_methods(
    activity_service, mock_user_service, mock_program_service, setup_mocks
):
    repo = activity_service.activity_repo
    repo.find_by_user_id_and_date.return_value = [Activity(id=1)]
    repo.find_by_user_id_and_slack_channel_and_date.return_value = [Activity(id=2)]
    repo.find_users_with_completed_program.return_value = [1]
    repo.find_by_id_and_slack_id.return_value = Activity(id=3)
    mock_program_service.find_by_name.return_value = Program(id=1, name="P")

    result_by_user = await activity_service.find_by_user("U", "2023-10")
    assert result_by_user[0].id == 1

    result_by_prog = await activity_service.find_by_user_and_program(
        "C", "U", "2023-10"
    )
    assert result_by_prog[0].id == 2

    result_all = await activity_service.find_all_user_by_program_completed(
        "P", "2023-10"
    )
    assert result_all == [1]

    result_id = await activity_service.find_by_id(1, "U")
    assert result_id.id == 3


@pytest.mark.anyio
async def test_validate_date_range(
    activity_service, mock_user_service, mock_program_service, today, setup_mocks
):
    program = _mock_setup_defaults(
        mock_user_service, mock_program_service, activity_service, today
    )

    await activity_service.create(
        ActivityCreate(description="R", performed_at=today), "C", "U"
    )

    program.end_date = today - timedelta(days=1)
    await _assert_error(
        activity_service.create(
            ActivityCreate(description="R", performed_at=today), "C", "U"
        ),
        BusinessRuleViolationError,
        "outside",
    )


@pytest.mark.anyio
async def test_validate_timezones(
    activity_service, mock_user_service, mock_program_service, setup_mocks, today
):
    _mock_setup_defaults(
        mock_user_service, mock_program_service, activity_service, today
    )
    tz = timezone(timedelta(hours=-3))
    now_tz = datetime.now(tz)

    program = Program(
        id=1,
        start_date=datetime(today.year, 1, 1),
        end_date=datetime(today.year, 12, 31),
    )
    mock_program_service.find_by_slack_channel.return_value = [program]

    await activity_service.create(
        ActivityCreate(description="R", performed_at=now_tz), "C", "U"
    )

    program.end_date = datetime(today.year, 12, 31)
    await activity_service.create(
        ActivityCreate(description="R", performed_at=now_tz), "C", "U"
    )


@pytest.mark.anyio
async def test_create_defaults_date_to_now(
    activity_service, mock_user_service, mock_program_service, setup_mocks, today
):
    _mock_setup_defaults(
        mock_user_service, mock_program_service, activity_service, today
    )
    await activity_service.create(
        ActivityCreate(description="R", performed_at=None), "C", "U"
    )
    created = activity_service.activity_repo.create.call_args[0][0]
    assert created.performed_at is not None


@pytest.mark.anyio
async def test_validate_performed_at_before_start_date(
    activity_service, mock_user_service, mock_program_service, setup_mocks, today
):
    program = _mock_setup_defaults(
        mock_user_service, mock_program_service, activity_service, today
    )
    program.start_date = today + timedelta(days=1)
    await _assert_error(
        activity_service.create(
            ActivityCreate(description="R", performed_at=today), "C", "U"
        ),
        BusinessRuleViolationError,
        "outside",
    )


@pytest.mark.anyio
async def test_validate_naive_activity_aware_start_date(
    activity_service, mock_user_service, mock_program_service, setup_mocks, today
):
    program = _mock_setup_defaults(
        mock_user_service, mock_program_service, activity_service, today
    )
    tz = timezone(timedelta(hours=-3))
    program.start_date = datetime(today.year, 1, 1).replace(tzinfo=tz)

    await activity_service.create(
        ActivityCreate(description="R", performed_at=today), "C", "U"
    )


@pytest.mark.anyio
async def test_validate_naive_activity_aware_end_date(
    activity_service, mock_user_service, mock_program_service, setup_mocks, today
):
    program = _mock_setup_defaults(
        mock_user_service, mock_program_service, activity_service, today
    )
    tz = timezone(timedelta(hours=-3))
    program.end_date = datetime(today.year + 1, 1, 1).replace(tzinfo=tz)

    await activity_service.create(
        ActivityCreate(description="R", performed_at=today), "C", "U"
    )
    created = activity_service.activity_repo.create.call_args[0][0]
    assert created.performed_at.tzinfo == tz


@pytest.mark.anyio
async def test_validate_timezone_aware_activity_naive_program_start(
    activity_service, mock_user_service, mock_program_service, setup_mocks
):
    past_naive = datetime.now() - timedelta(days=1)

    naive_start = datetime(past_naive.year, 1, 1)

    mock_user_service.find_by_slack_id.return_value = User(id=1)

    program = Program(
        id=1, start_date=naive_start, end_date=datetime(past_naive.year + 1, 1, 1)
    )
    mock_program_service.find_by_slack_channel.return_value = [program]

    activity_service.activity_repo.check_activity_same_day.return_value = None
    activity_service.activity_repo.count_monthly.return_value = 1

    async def assign_id(act):
        act.id = 1

    activity_service.activity_repo.create.side_effect = assign_id

    activity_create = ActivityCreate(description="R", performed_at=past_naive)
    activity_create.performed_at = past_naive

    await activity_service.create(activity_create, "C", "U")

    activity_service.activity_repo.create.assert_called_once()


@pytest.mark.anyio
async def test_validate_timezone_aware_activity_naive_program_end(
    activity_service, mock_user_service, mock_program_service, setup_mocks
):
    past_naive = datetime.now() - timedelta(days=1)

    mock_user_service.find_by_slack_id.return_value = User(id=1)

    naive_start = datetime(past_naive.year, 1, 1)
    naive_end = datetime(past_naive.year + 1, 1, 1)

    program = Program(id=1, start_date=naive_start, end_date=naive_end)
    mock_program_service.find_by_slack_channel.return_value = [program]

    activity_service.activity_repo.check_activity_same_day.return_value = None
    activity_service.activity_repo.count_monthly.return_value = 1

    async def assign_id(act):
        act.id = 1

    activity_service.activity_repo.create.side_effect = assign_id

    activity_create = ActivityCreate(description="R", performed_at=past_naive)
    activity_create.performed_at = past_naive

    await activity_service.create(activity_create, "C", "U")

    activity_service.activity_repo.create.assert_called_once()


@pytest.mark.anyio
async def test_validate_timezone_aware_activity_aware_program_start(
    activity_service, mock_user_service, mock_program_service, setup_mocks
):
    tz = timezone(timedelta(hours=-3))
    past_naive = datetime.now() - timedelta(days=1)

    mock_user_service.find_by_slack_id.return_value = User(id=1)

    aware_start = datetime(past_naive.year, 1, 1, tzinfo=tz)
    aware_end = datetime(past_naive.year + 1, 1, 1, tzinfo=tz)

    program = Program(id=1, start_date=aware_start, end_date=aware_end)
    mock_program_service.find_by_slack_channel.return_value = [program]

    activity_service.activity_repo.check_activity_same_day.return_value = None
    activity_service.activity_repo.count_monthly.return_value = 1

    async def assign_id(act):
        act.id = 1

    activity_service.activity_repo.create.side_effect = assign_id

    activity_create = ActivityCreate(description="R", performed_at=past_naive)
    activity_create.performed_at = past_naive

    await activity_service.create(activity_create, "C", "U")

    activity_service.activity_repo.create.assert_called_once()
