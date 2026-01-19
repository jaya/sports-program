import logging
import uuid

from slack_sdk.oauth.installation_store import Installation
from slack_sdk.oauth.installation_store.async_installation_store import (
    AsyncInstallationStore,
)
from slack_sdk.oauth.state_store.async_state_store import AsyncOAuthStateStore

from app.repositories.slack_installation_repository import SlackInstallationRepository
from app.repositories.slack_state_repository import SlackStateRepository
from app.services.slack_oauth_service import SlackOAuthService

logger = logging.getLogger(__name__)


class SQLAlchemyInstallationStore(AsyncInstallationStore):
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def async_save(self, installation: Installation):
        async with self.session_factory() as session:
            repo = SlackInstallationRepository(session)
            state_repo = SlackStateRepository(session)
            service = SlackOAuthService(repo, state_repo)
            await service.save_installation(installation)

    async def async_find_bot(
        self,
        *,
        enterprise_id: str | None,
        team_id: str | None,
        is_enterprise_install: bool | None = False,
    ) -> Installation | None:
        async with self.session_factory() as session:
            repo = SlackInstallationRepository(session)
            state_repo = SlackStateRepository(session)
            service = SlackOAuthService(repo, state_repo)
            db_install = await service.find_installation(enterprise_id, team_id)

            if db_install:
                return Installation(
                    app_id=None,
                    enterprise_id=db_install.enterprise_id,
                    team_id=db_install.team_id,
                    bot_token=db_install.bot_token,
                    bot_id=db_install.bot_id,
                    bot_user_id=db_install.bot_user_id,
                    bot_scopes=(
                        db_install.scope.split(",") if db_install.scope else []
                    ),
                    user_id=db_install.installer_user_id,
                    is_enterprise_install=db_install.is_enterprise_install,
                )
        return None


class SQLAlchemyStateStore(AsyncOAuthStateStore):
    def __init__(self, session_factory, expiration_seconds: int):
        self.session_factory = session_factory
        self.expiration_seconds = expiration_seconds

    async def async_issue(self, *args, **kwargs) -> str:
        state = str(uuid.uuid4())
        async with self.session_factory() as session:
            repo = SlackInstallationRepository(session)
            state_repo = SlackStateRepository(session)
            service = SlackOAuthService(repo, state_repo)
            return await service.issue_state(state, self.expiration_seconds)

    async def async_consume(self, state: str) -> bool:
        async with self.session_factory() as session:
            repo = SlackInstallationRepository(session)
            state_repo = SlackStateRepository(session)
            service = SlackOAuthService(repo, state_repo)
            return await service.consume_state(state)
