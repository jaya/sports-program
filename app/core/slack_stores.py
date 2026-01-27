import uuid
from contextlib import asynccontextmanager

import structlog
from slack_sdk.oauth.installation_store import Installation
from slack_sdk.oauth.installation_store.async_installation_store import (
    AsyncInstallationStore,
)
from slack_sdk.oauth.state_store.async_state_store import AsyncOAuthStateStore

from app.repositories.slack_installation_repository import SlackInstallationRepository
from app.repositories.slack_state_repository import SlackStateRepository
from app.services.slack_oauth_service import SlackOAuthService

logger = structlog.get_logger()


@asynccontextmanager
async def slack_oauth_context(session_factory):
    """
    Asynchronous context manager to initialize the Slack OAuth architecture.

    It centralizes the creation of repositories and the service within a single
    database session, ensuring consistent transactional behavior and reducing
    code duplication across various store methods.
    """
    async with session_factory() as session:
        repo = SlackInstallationRepository(session)
        state_repo = SlackStateRepository(session)
        yield SlackOAuthService(repo, state_repo)


class SQLAlchemyInstallationStore(AsyncInstallationStore):
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def async_save(self, installation: Installation):
        try:
            async with slack_oauth_context(self.session_factory) as service:
                await service.save_installation(installation)
        except Exception as e:
            logger.error(
                "Failed to save Slack installation",
                team_id=installation.team_id,
                error=str(e),
                exc_info=True,
            )
            raise

    async def async_find_bot(
        self,
        *,
        enterprise_id: str | None,
        team_id: str | None,
        is_enterprise_install: bool | None = False,
    ) -> Installation | None:
        try:
            async with slack_oauth_context(self.session_factory) as service:
                return await service.get_bot(enterprise_id, team_id)
        except Exception as e:
            logger.error(
                "Failed to find Slack bot",
                team_id=team_id,
                enterprise_id=enterprise_id,
                error=str(e),
                exc_info=True,
            )
            return None


class SQLAlchemyStateStore(AsyncOAuthStateStore):
    def __init__(self, session_factory, expiration_seconds: int):
        self.session_factory = session_factory
        self.expiration_seconds = expiration_seconds

    async def async_issue(self, *args, **kwargs) -> str:
        state = str(uuid.uuid4())
        try:
            async with slack_oauth_context(self.session_factory) as service:
                return await service.issue_state(state, self.expiration_seconds)
        except Exception as e:
            logger.error(
                "Failed to issue Slack OAuth state",
                error=str(e),
                exc_info=True,
            )
            raise

    async def async_consume(self, state: str) -> bool:
        try:
            async with slack_oauth_context(self.session_factory) as service:
                return await service.consume_state(state)
        except Exception as e:
            logger.error(
                "Failed to consume Slack OAuth state",
                state=state,
                error=str(e),
                exc_info=True,
            )
            return False
