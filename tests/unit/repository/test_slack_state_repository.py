from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.slack_installation import SlackState
from app.repositories.slack_state_repository import SlackStateRepository


@pytest.mark.anyio
async def test_slack_state_repository_find_by_state():
    session = AsyncMock(spec=AsyncSession)
    repo = SlackStateRepository(session)
    state_obj = SlackState(id=1, state="state123")

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = state_obj
    session.execute.return_value = mock_result

    result = await repo.find_by_state("state123")

    session.execute.assert_called_once()
    assert result == state_obj
    assert result.state == "state123"


@pytest.mark.anyio
async def test_slack_state_repository_delete_by_state():
    session = AsyncMock(spec=AsyncSession)
    repo = SlackStateRepository(session)
    state_obj = SlackState(id=1, state="state123")

    # Mock find_by_state
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = state_obj
    session.execute.return_value = mock_result

    await repo.delete_by_state("state123")

    session.delete.assert_called_once_with(state_obj)
    session.commit.assert_called_once()
