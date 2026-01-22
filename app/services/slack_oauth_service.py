import logging
from datetime import UTC, datetime

from slack_sdk.oauth.installation_store import Installation

from app.models.slack_installation import SlackInstallation, SlackState
from app.repositories.slack_installation_repository import SlackInstallationRepository
from app.repositories.slack_state_repository import SlackStateRepository

logger = logging.getLogger(__name__)


class SlackOAuthService:
    def __init__(
        self,
        installation_repo: SlackInstallationRepository,
        state_repo: SlackStateRepository,
    ):
        self.installation_repo = installation_repo
        self.state_repo = state_repo

    async def save_installation(self, installation: Installation) -> None:
        db_installation = await self.installation_repo.get_by_team_or_enterprise(
            installation.team_id, installation.enterprise_id
        )

        scope = ",".join(installation.bot_scopes) if installation.bot_scopes else None

        if not db_installation:
            db_installation = SlackInstallation(
                team_id=installation.team_id,
                enterprise_id=installation.enterprise_id,
                is_enterprise_install=installation.is_enterprise_install,
                bot_token=installation.bot_token,
                bot_id=installation.bot_id,
                bot_user_id=installation.bot_user_id,
                installer_user_id=installation.user_id,
                scope=scope,
            )
            logger.info(
                "Creating new Slack installation for team %s (enterprise: %s)",
                installation.team_id,
                installation.enterprise_id,
            )
            await self.installation_repo.create(db_installation)
        else:
            db_installation.bot_token = installation.bot_token
            db_installation.bot_id = installation.bot_id
            db_installation.bot_user_id = installation.bot_user_id
            db_installation.installer_user_id = installation.user_id
            db_installation.scope = scope

            logger.info(
                "Updating Slack installation for team %s (enterprise: %s)",
                installation.team_id,
                installation.enterprise_id,
            )
            await self.installation_repo.update(db_installation)

    async def find_installation(
        self, enterprise_id: str | None, team_id: str | None
    ) -> SlackInstallation | None:
        return await self.installation_repo.get_by_team_or_enterprise(
            team_id, enterprise_id
        )

    async def get_bot(
        self, enterprise_id: str | None, team_id: str | None
    ) -> Installation | None:
        db_install = await self.find_installation(enterprise_id, team_id)
        if not db_install:
            logger.debug(
                "Bot not found for team %s (enterprise: %s)", team_id, enterprise_id
            )
            return None

        return Installation(
            app_id=None,
            enterprise_id=db_install.enterprise_id,
            team_id=db_install.team_id,
            bot_token=db_install.bot_token,
            bot_id=db_install.bot_id,
            bot_user_id=db_install.bot_user_id,
            bot_scopes=(db_install.scope.split(",") if db_install.scope else []),
            user_id=db_install.installer_user_id,
            is_enterprise_install=db_install.is_enterprise_install,
        )

    async def issue_state(self, state: str, expiration_seconds: int) -> str:
        expire_at = datetime.fromtimestamp(
            datetime.now(UTC).timestamp() + expiration_seconds,
            tz=UTC,
        )
        db_state = SlackState(state=state, expire_at=expire_at)
        logger.info("Issued Slack OAuth state: %s (expires: %s)", state, expire_at)
        await self.state_repo.create(db_state)
        return state

    async def consume_state(self, state: str) -> bool:
        db_state = await self.state_repo.find_by_state(state)
        if db_state:
            is_valid = db_state.expire_at > datetime.now(UTC)
            logger.info("Consuming Slack OAuth state: %s. Valid: %s", state, is_valid)
            await self.state_repo.delete_by_state(state)
            return is_valid
        logger.warning("Attempted to consume non-existent Slack OAuth state: %s", state)
        return False
