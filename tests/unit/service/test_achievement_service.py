from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.exceptions.business import (
    DatabaseError,
    EntityNotFoundError,
    ExternalServiceError,
)
from app.models.achievement import Achievement
from app.models.program import Program
from app.models.user import User
from app.repositories.achievement_repository import AchievementRepository
from app.repositories.program_repository import ProgramRepository
from app.repositories.user_repository import UserRepository
from app.schemas.achievement import AchievementBatchCreate, AchievementCreate
from app.services.achievement_service import AchievementService


@pytest.fixture
def mock_achievement_repo():
    return AsyncMock(spec=AchievementRepository)


@pytest.fixture
def mock_user_repo():
    return AsyncMock(spec=UserRepository)


@pytest.fixture
def mock_program_repo():
    return AsyncMock(spec=ProgramRepository)


@pytest.fixture
def service(mock_achievement_repo, mock_user_repo, mock_program_repo):
    return AchievementService(
        achievement_repo=mock_achievement_repo,
        user_repo=mock_user_repo,
        program_repo=mock_program_repo,
    )


@pytest.mark.anyio
async def test_achievement_service_create_success(service, mock_achievement_repo):
    achievement_create = AchievementCreate(cycle_reference="2023-10")
    expected_achievement = Achievement(
        id=1, user_id=1, program_id=1, cycle_reference="2023-10"
    )
    mock_achievement_repo.create.return_value = expected_achievement

    result = await service.create(achievement_create, program_id=1, user_id=1)

    assert result == expected_achievement
    mock_achievement_repo.create.assert_called_once()


@pytest.mark.anyio
async def test_achievement_service_create_database_error(
    service, mock_achievement_repo
):
    achievement_create = AchievementCreate(cycle_reference="2023-10")
    mock_achievement_repo.create.side_effect = Exception("DB Fail")

    with pytest.raises(DatabaseError):
        await service.create(achievement_create, program_id=1, user_id=1)


@pytest.mark.anyio
async def test_achievement_service_create_batch_success(
    service, mock_achievement_repo, mock_user_repo
):
    batch_create = AchievementBatchCreate(
        program_id=1, user_ids=[1, 2], cycle_reference="2023-10", program_name="Test"
    )

    # Mock no existing achievements
    mock_achievement_repo.find_existing_user_ids.return_value = set()
    # Mock user name fetching
    mock_user_repo.find_all_by_ids.return_value = [
        User(id=1, display_name="User 1"),
        User(id=2, display_name="User 2"),
    ]

    result = await service.create_batch(batch_create)

    assert result.total_created == 2
    assert result.program_name == "Test"
    assert "User 1" in result.users
    assert "User 2" in result.users
    mock_achievement_repo.find_existing_user_ids.assert_called_once()
    mock_achievement_repo.create_many.assert_called_once()


@pytest.mark.anyio
async def test_achievement_service_create_batch_some_already_exist(
    service, mock_achievement_repo, mock_user_repo, caplog
):
    batch_create = AchievementBatchCreate(
        program_id=1, user_ids=[1, 2], cycle_reference="2023-10", program_name="Test"
    )

    # User 1 already has achievement
    mock_achievement_repo.find_existing_user_ids.return_value = {1}
    mock_user_repo.find_all_by_ids.return_value = [
        User(id=2, display_name="User 2"),
    ]

    result = await service.create_batch(batch_create)

    assert result.total_created == 1
    assert "User 2" in result.users
    assert "User 1" not in result.users

    mock_achievement_repo.create_many.assert_called_once()
    args, _ = mock_achievement_repo.create_many.call_args
    assert len(args[0]) == 1
    assert args[0][0].user_id == 2


@pytest.mark.anyio
async def test_achievement_service_create_batch_database_error(
    service, mock_achievement_repo
):
    batch_create = AchievementBatchCreate(
        program_id=1, user_ids=[1], cycle_reference="2023-10", program_name="Test"
    )

    mock_achievement_repo.find_existing_user_ids.return_value = set()
    mock_achievement_repo.create_many.side_effect = Exception("DB Error")

    with pytest.raises(DatabaseError):
        await service.create_batch(batch_create)


@pytest.mark.anyio
async def test_achievement_service_create_batch_all_already_exist(
    service, mock_achievement_repo, mock_user_repo
):
    batch_create = AchievementBatchCreate(
        program_id=1, user_ids=[1], cycle_reference="2023-10", program_name="Test"
    )

    # All users already have achievement
    mock_achievement_repo.find_existing_user_ids.return_value = {1}

    result = await service.create_batch(batch_create)

    assert result.total_created == 0
    assert result.users == []
    mock_achievement_repo.create_many.assert_not_called()
    mock_user_repo.find_all_by_ids.assert_not_called()


@pytest.mark.anyio
async def test_notify_achievements_program_not_found(service, mock_program_repo):
    mock_program_repo.find_by_name.return_value = None

    with pytest.raises(EntityNotFoundError):
        await service.notify_achievements(program_name="Unknown", cycle_reference="2023-10")


@pytest.mark.anyio
async def test_notify_achievements_no_pending(
    service, mock_program_repo, mock_achievement_repo
):
    mock_program_repo.find_by_name.return_value = Program(id=1, name="Test")
    mock_achievement_repo.find_pending_notification.return_value = []

    result = await service.notify_achievements(program_name="Test", cycle_reference="2023-10")

    assert result.total_notified == 0
    assert "No pending" in result.message


@pytest.mark.anyio
async def test_notify_achievements_success(service, mock_program_repo, mock_achievement_repo):
    with patch("app.services.achievement_service.slack_app") as mock_slack:
        program = Program(id=1, name="Challenge", slack_channel="C123")
        user1 = User(id=1, slack_id="U111", display_name="John")
        user2 = User(id=2, slack_id="U222", display_name="Jane")

        achievement1 = MagicMock()
        achievement1.id = 1
        achievement1.user = user1
        achievement1.program = program

        achievement2 = MagicMock()
        achievement2.id = 2
        achievement2.user = user2
        achievement2.program = program

        mock_program_repo.find_by_name.return_value = program
        mock_achievement_repo.find_pending_notification.return_value = [
            achievement1, achievement2
        ]
        mock_slack.client.chat_postMessage = AsyncMock()
        mock_achievement_repo.mark_as_notified = AsyncMock()

        result = await service.notify_achievements(
            program_name="Challenge", cycle_reference="2023-10"
        )

        assert result.total_notified == 2
        assert "John" in result.users
        assert "Jane" in result.users
        assert "<@U111>" in result.message
        assert "<@U222>" in result.message
        mock_slack.client.chat_postMessage.assert_called_once()
        mock_achievement_repo.mark_as_notified.assert_called_once_with([1, 2])


@pytest.mark.anyio
async def test_notify_achievements_slack_error(service, mock_program_repo, mock_achievement_repo):
    with patch("app.services.achievement_service.slack_app") as mock_slack:
        program = Program(id=1, name="Challenge", slack_channel="C123")
        user = User(id=1, slack_id="U111", display_name="John")

        achievement = MagicMock()
        achievement.id = 1
        achievement.user = user
        achievement.program = program

        mock_program_repo.find_by_name.return_value = program
        mock_achievement_repo.find_pending_notification.return_value = [achievement]
        mock_slack.client.chat_postMessage = AsyncMock(
            side_effect=Exception("Slack API Error")
        )

        with pytest.raises(ExternalServiceError) as exc_info:
            await service.notify_achievements(
                program_name="Challenge", cycle_reference="2023-10"
            )

        assert "Slack" in str(exc_info.value.message)
