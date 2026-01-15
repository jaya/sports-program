from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

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
