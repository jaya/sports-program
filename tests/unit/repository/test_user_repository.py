import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import UserRepository
from app.models.user import User

@pytest.mark.anyio
async def test_user_repository_find_by_slack_id():
    session = AsyncMock(spec=AsyncSession)
    repo = UserRepository(session)
    user = User(id=1, slack_id="U123", display_name="Test User")
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = user
    session.execute.return_value = mock_result
    
    result = await repo.find_by_slack_id("U123")
    
    session.execute.assert_called_once()
    assert result == user
    assert result.slack_id == "U123"

@pytest.mark.anyio
async def test_user_repository_find_by_slack_id_not_found():
    session = AsyncMock(spec=AsyncSession)
    repo = UserRepository(session)
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    session.execute.return_value = mock_result
    
    result = await repo.find_by_slack_id("U999")
    
    assert result is None
