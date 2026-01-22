from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from slack_sdk.oauth.installation_store import Installation

from app.models.slack_installation import SlackInstallation, SlackState
from app.repositories.slack_installation_repository import SlackInstallationRepository
from app.repositories.slack_state_repository import SlackStateRepository
from app.services.slack_oauth_service import SlackOAuthService


@pytest.fixture
def mock_installation_repo():
    return AsyncMock(spec=SlackInstallationRepository)


@pytest.fixture
def mock_state_repo():
    return AsyncMock(spec=SlackStateRepository)


@pytest.fixture
def slack_oauth_service(mock_installation_repo, mock_state_repo):
    return SlackOAuthService(
        installation_repo=mock_installation_repo, state_repo=mock_state_repo
    )


@pytest.mark.anyio
async def test_save_installation_new(slack_oauth_service, mock_installation_repo):
    installation = Installation(
        team_id="T123",
        bot_token="xoxb-123",
        bot_id="B123",
        bot_user_id="U123",
        user_id="U456",
        bot_scopes=["commands", "chat:write"],
    )
    mock_installation_repo.get_by_team_or_enterprise.return_value = None

    await slack_oauth_service.save_installation(installation)

    mock_installation_repo.create.assert_called_once()
    mock_installation_repo.update.assert_not_called()
    # Check if correct attributes were mapped
    args = mock_installation_repo.create.call_args[0][0]
    assert args.team_id == "T123"


@pytest.mark.anyio
async def test_issue_state(slack_oauth_service, mock_state_repo):
    state = "state123"
    expiration = 600

    result = await slack_oauth_service.issue_state(state, expiration)

    assert result == state
    mock_state_repo.create.assert_called_once()
    state_obj = mock_state_repo.create.call_args[0][0]
    assert state_obj.state == state
    assert isinstance(state_obj.expire_at, datetime)


@pytest.mark.anyio
async def test_consume_state_valid(slack_oauth_service, mock_state_repo):
    state = "state123"
    db_state = SlackState(
        state=state,
        expire_at=datetime.fromtimestamp(datetime.now(UTC).timestamp() + 100, tz=UTC),
    )
    mock_state_repo.find_by_state.return_value = db_state

    result = await slack_oauth_service.consume_state(state)

    assert result is True
    mock_state_repo.delete_by_state.assert_called_once_with(state)


@pytest.mark.anyio
async def test_consume_state_expired(slack_oauth_service, mock_state_repo):
    state = "state123"
    db_state = SlackState(
        state=state,
        expire_at=datetime.fromtimestamp(datetime.now(UTC).timestamp() - 100, tz=UTC),
    )
    mock_state_repo.find_by_state.return_value = db_state

    result = await slack_oauth_service.consume_state(state)

    assert result is False
    mock_state_repo.delete_by_state.assert_called_once_with(state)


@pytest.mark.anyio
async def test_get_bot_success(slack_oauth_service, mock_installation_repo):
    db_install = SlackInstallation(
        team_id="T123",
        bot_token="xoxb-123",
        scope="commands,chat:write",
        installer_user_id="U456",
    )
    mock_installation_repo.get_by_team_or_enterprise.return_value = db_install

    result = await slack_oauth_service.get_bot(None, "T123")

    assert isinstance(result, Installation)
    assert result.team_id == "T123"
    assert result.bot_token == "xoxb-123"
    assert result.bot_scopes == ["commands", "chat:write"]


@pytest.mark.anyio
async def test_get_bot_not_found(slack_oauth_service, mock_installation_repo):
    mock_installation_repo.get_by_team_or_enterprise.return_value = None

    result = await slack_oauth_service.get_bot(None, "T999")

    assert result is None
