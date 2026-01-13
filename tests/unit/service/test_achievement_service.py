from unittest.mock import AsyncMock, MagicMock

import pytest

from app.exceptions.business import DatabaseError
from app.models.achievement import Achievement
from app.models.user import User
from app.repositories.achievement_repository import AchievementRepository
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
def service(mock_achievement_repo, mock_user_repo):
    return AchievementService(
        achievement_repo=mock_achievement_repo, user_repo=mock_user_repo
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
    assert "Achievement already exists for user 1" in caplog.text

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
