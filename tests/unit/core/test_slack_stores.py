from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from slack_sdk.oauth.installation_store import Installation

from app.core.slack_stores import SQLAlchemyInstallationStore, SQLAlchemyStateStore


@pytest.mark.anyio
async def test_sqlalchemy_installation_store_async_save_success():
    session_factory = MagicMock()
    store = SQLAlchemyInstallationStore(session_factory)
    installation = MagicMock(spec=Installation)
    installation.team_id = "T123"

    with patch("app.core.slack_stores.slack_oauth_context") as mock_context:
        mock_service = AsyncMock()
        mock_context.return_value.__aenter__.return_value = mock_service

        await store.async_save(installation)

        mock_service.save_installation.assert_called_once_with(installation)


@pytest.mark.anyio
async def test_sqlalchemy_installation_store_async_save_failure():
    session_factory = MagicMock()
    store = SQLAlchemyInstallationStore(session_factory)
    installation = MagicMock(spec=Installation)
    installation.team_id = "T123"

    with patch("app.core.slack_stores.slack_oauth_context") as mock_context:
        mock_service = AsyncMock()
        mock_context.return_value.__aenter__.return_value = mock_service
        mock_service.save_installation.side_effect = Exception("DB Error")

        with pytest.raises(Exception, match="DB Error"):
            await store.async_save(installation)


@pytest.mark.anyio
async def test_sqlalchemy_installation_store_async_find_bot_success():
    session_factory = MagicMock()
    store = SQLAlchemyInstallationStore(session_factory)
    installation = MagicMock(spec=Installation)

    with patch("app.core.slack_stores.slack_oauth_context") as mock_context:
        mock_service = AsyncMock()
        mock_context.return_value.__aenter__.return_value = mock_service
        mock_service.get_bot.return_value = installation

        result = await store.async_find_bot(enterprise_id="E123", team_id="T123")

        assert result == installation
        mock_service.get_bot.assert_called_once_with("E123", "T123")


@pytest.mark.anyio
async def test_sqlalchemy_installation_store_async_find_bot_failure_returns_none():
    session_factory = MagicMock()
    store = SQLAlchemyInstallationStore(session_factory)

    with patch("app.core.slack_stores.slack_oauth_context") as mock_context:
        mock_service = AsyncMock()
        mock_context.return_value.__aenter__.return_value = mock_service
        mock_service.get_bot.side_effect = Exception("DB Error")

        result = await store.async_find_bot(enterprise_id="E123", team_id="T123")

        assert result is None


@pytest.mark.anyio
async def test_sqlalchemy_state_store_async_issue_success():
    session_factory = MagicMock()
    store = SQLAlchemyStateStore(session_factory, expiration_seconds=600)

    with patch("app.core.slack_stores.slack_oauth_context") as mock_context:
        mock_service = AsyncMock()
        mock_context.return_value.__aenter__.return_value = mock_service
        mock_service.issue_state.return_value = "state123"

        result = await store.async_issue()

        assert result == "state123"
        mock_service.issue_state.assert_called_once()


@pytest.mark.anyio
async def test_sqlalchemy_state_store_async_issue_failure():
    session_factory = MagicMock()
    store = SQLAlchemyStateStore(session_factory, expiration_seconds=600)

    with patch("app.core.slack_stores.slack_oauth_context") as mock_context:
        mock_service = AsyncMock()
        mock_context.return_value.__aenter__.return_value = mock_service
        mock_service.issue_state.side_effect = Exception("DB Error")

        with pytest.raises(Exception, match="DB Error"):
            await store.async_issue()


@pytest.mark.anyio
async def test_sqlalchemy_state_store_async_consume_success():
    session_factory = MagicMock()
    store = SQLAlchemyStateStore(session_factory, expiration_seconds=600)

    with patch("app.core.slack_stores.slack_oauth_context") as mock_context:
        mock_service = AsyncMock()
        mock_context.return_value.__aenter__.return_value = mock_service
        mock_service.consume_state.return_value = True

        result = await store.async_consume("state123")

        assert result is True
        mock_service.consume_state.assert_called_once_with("state123")


@pytest.mark.anyio
async def test_sqlalchemy_state_store_async_consume_failure_returns_false():
    session_factory = MagicMock()
    store = SQLAlchemyStateStore(session_factory, expiration_seconds=600)

    with patch("app.core.slack_stores.slack_oauth_context") as mock_context:
        mock_service = AsyncMock()
        mock_context.return_value.__aenter__.return_value = mock_service
        mock_service.consume_state.side_effect = Exception("DB Error")

        result = await store.async_consume("state123")

        assert result is False
