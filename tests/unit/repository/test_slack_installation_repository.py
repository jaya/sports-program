from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.slack_installation import SlackInstallation
from app.repositories.slack_installation_repository import SlackInstallationRepository


@pytest.mark.anyio
async def test_slack_installation_repository_find_by_team_id():
    session = AsyncMock(spec=AsyncSession)
    repo = SlackInstallationRepository(session)
    installation = SlackInstallation(id=1, team_id="T123", bot_token="xoxb-123")

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = installation
    session.execute.return_value = mock_result

    result = await repo.find_by_team_id("T123")

    session.execute.assert_called_once()
    assert result == installation
    assert result.team_id == "T123"


@pytest.mark.anyio
async def test_slack_installation_repository_find_org_wide_install():
    session = AsyncMock(spec=AsyncSession)
    repo = SlackInstallationRepository(session)
    installation = SlackInstallation(
        id=1, enterprise_id="E123", is_enterprise_install=True
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = installation
    session.execute.return_value = mock_result

    result = await repo.find_org_wide_install("E123")

    session.execute.assert_called_once()
    assert result == installation
    assert result.enterprise_id == "E123"
    assert result.is_enterprise_install is True


@pytest.mark.anyio
async def test_slack_installation_repository_get_by_team_or_enterprise_team_priority():
    session = AsyncMock(spec=AsyncSession)
    repo = SlackInstallationRepository(session)
    installation = SlackInstallation(id=1, team_id="T123")

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = installation
    session.execute.return_value = mock_result

    result = await repo.get_by_team_or_enterprise("T123", "E123")

    assert result == installation
    assert result.team_id == "T123"
    # Should stop after finding by team
    assert session.execute.call_count == 1
