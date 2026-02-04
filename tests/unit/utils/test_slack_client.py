from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.program import Program
from app.models.slack_installation import SlackInstallation
from app.utils.slack_client import get_slack_client_for_program


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def program_with_team_id():
    return Program(
        id=1,
        name="Test Program",
        slack_channel="C123",
        team_id="T123",
        enterprise_id=None,
    )


@pytest.fixture
def program_with_enterprise_id():
    return Program(
        id=2,
        name="Enterprise Program",
        slack_channel="C456",
        team_id=None,
        enterprise_id="E456",
    )


@pytest.fixture
def program_without_ids():
    return Program(
        id=3,
        name="No IDs Program",
        slack_channel="C789",
        team_id=None,
        enterprise_id=None,
    )


@pytest.fixture
def slack_installation():
    return SlackInstallation(
        id=1,
        team_id="T123",
        enterprise_id=None,
        bot_token="xoxb-test-token",
        bot_user_id="U123",
    )


@pytest.mark.anyio
async def test_get_slack_client_for_program_success(
    mock_db, program_with_team_id, slack_installation
):
    with patch(
        "app.utils.slack_client.SlackInstallationRepository"
    ) as mock_repo_class:
        mock_repo = AsyncMock()
        mock_repo.get_by_team_or_enterprise.return_value = slack_installation
        mock_repo_class.return_value = mock_repo

        async with get_slack_client_for_program(
            mock_db, program_with_team_id
        ) as client:
            assert client is not None
            assert client.token == "xoxb-test-token"

        mock_repo.get_by_team_or_enterprise.assert_called_once_with(
            "T123", None)


@pytest.mark.anyio
async def test_get_slack_client_for_program_with_enterprise_id(
    mock_db, program_with_enterprise_id, slack_installation
):
    slack_installation.team_id = None
    slack_installation.enterprise_id = "E456"

    with patch(
        "app.utils.slack_client.SlackInstallationRepository"
    ) as mock_repo_class:
        mock_repo = AsyncMock()
        mock_repo.get_by_team_or_enterprise.return_value = slack_installation
        mock_repo_class.return_value = mock_repo

        async with get_slack_client_for_program(
            mock_db, program_with_enterprise_id
        ) as client:
            assert client is not None

        mock_repo.get_by_team_or_enterprise.assert_called_once_with(
            None, "E456")


@pytest.mark.anyio
async def test_get_slack_client_for_program_no_ids_returns_none(
    mock_db, program_without_ids
):
    async with get_slack_client_for_program(mock_db, program_without_ids) as client:
        assert client is None


@pytest.mark.anyio
async def test_get_slack_client_for_program_installation_not_found(
    mock_db, program_with_team_id
):
    with patch(
        "app.utils.slack_client.SlackInstallationRepository"
    ) as mock_repo_class:
        mock_repo = AsyncMock()
        mock_repo.get_by_team_or_enterprise.return_value = None
        mock_repo_class.return_value = mock_repo

        async with get_slack_client_for_program(
            mock_db, program_with_team_id
        ) as client:
            assert client is None


@pytest.mark.anyio
async def test_get_slack_client_for_program_closes_session():
    mock_db = AsyncMock()
    program = Program(
        id=1, name="Test", slack_channel="C123", team_id="T123", enterprise_id=None
    )
    installation = SlackInstallation(
        id=1,
        team_id="T123",
        enterprise_id=None,
        bot_token="xoxb-test",
        bot_user_id="U123",
    )

    with patch(
        "app.utils.slack_client.SlackInstallationRepository"
    ) as mock_repo_class:
        mock_repo = AsyncMock()
        mock_repo.get_by_team_or_enterprise.return_value = installation
        mock_repo_class.return_value = mock_repo

        with patch("app.utils.slack_client.AsyncWebClient") as mock_client_class:
            mock_client = MagicMock()
            mock_session = AsyncMock()
            mock_client.session = mock_session
            mock_client.token = "xoxb-test"
            mock_client_class.return_value = mock_client

            async with get_slack_client_for_program(mock_db, program) as client:
                assert client is not None

            mock_session.close.assert_called_once()
