from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.achievement import Achievement
from app.models.program import Program
from app.models.user import User
from app.repositories.achievement_repository import AchievementRepository


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repo(mock_session):
    return AchievementRepository(mock_session)


@pytest.mark.anyio
async def test_achievement_repository_find_existing_user_ids(repo, mock_session):
    # Mock result for existing achievements
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [1, 2]
    mock_session.execute.return_value = mock_result

    result = await repo.find_existing_user_ids(
        program_id=1, cycle_reference="2023-10", user_ids=[1, 2, 3]
    )

    assert result == {1, 2}
    mock_session.execute.assert_called_once()


@pytest.mark.anyio
async def test_find_pending_notification_returns_achievements(repo, mock_session):
    user = User(id=1, slack_id="U123", display_name="John")
    program = Program(id=1, name="Challenge")
    achievement = Achievement(
        id=1, user_id=1, program_id=1, cycle_reference="2023-10", is_notified=False
    )
    achievement.user = user
    achievement.program = program

    mock_result = MagicMock()
    mock_result.scalars.return_value.unique.return_value.all.return_value = [
        achievement]
    mock_session.execute.return_value = mock_result

    result = await repo.find_pending_notification(
        program_id=1, cycle_reference="2023-10"
    )

    assert len(result) == 1
    assert result[0].id == 1
    assert result[0].user.display_name == "John"
    mock_session.execute.assert_called_once()


@pytest.mark.anyio
async def test_find_pending_notification_returns_empty(repo, mock_session):
    mock_result = MagicMock()
    mock_result.scalars.return_value.unique.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result

    result = await repo.find_pending_notification(
        program_id=1, cycle_reference="2023-10"
    )

    assert result == []


@pytest.mark.anyio
async def test_mark_as_notified_success(repo, mock_session):
    mock_result = MagicMock()
    mock_result.rowcount = 3
    mock_session.execute.return_value = mock_result

    result = await repo.mark_as_notified([1, 2, 3])

    assert result == 3
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.anyio
async def test_mark_as_notified_empty_list(repo, mock_session):
    result = await repo.mark_as_notified([])

    assert result == 0
    mock_session.execute.assert_not_called()
    mock_session.commit.assert_not_called()
