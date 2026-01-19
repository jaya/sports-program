from datetime import datetime

from slack_sdk.oauth.installation_store import Installation

from app.models.slack_installation import SlackInstallation, SlackState
from app.repositories.slack_installation_repository import SlackInstallationRepository
from app.repositories.slack_state_repository import SlackStateRepository


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

        if not db_installation:
            db_installation = SlackInstallation(
                team_id=installation.team_id,
                enterprise_id=installation.enterprise_id,
                is_enterprise_install=installation.is_enterprise_install,
            )
            await self.installation_repo.create(db_installation)

        db_installation.bot_token = installation.bot_token
        db_installation.bot_id = installation.bot_id
        db_installation.bot_user_id = installation.bot_user_id
        db_installation.installer_user_id = installation.user_id
        db_installation.scope = (
            ",".join(installation.bot_scopes) if installation.bot_scopes else None
        )

        await self.installation_repo.update(db_installation)

    async def find_installation(
        self, enterprise_id: str | None, team_id: str | None
    ) -> SlackInstallation | None:
        return await self.installation_repo.get_by_team_or_enterprise(
            team_id, enterprise_id
        )

    async def issue_state(self, state: str, expiration_seconds: int) -> str:
        expire_at = datetime.fromtimestamp(
            datetime.now().timestamp() + expiration_seconds
        )
        db_state = SlackState(state=state, expire_at=expire_at)
        await self.state_repo.create(db_state)
        return state

    async def consume_state(self, state: str) -> bool:
        db_state = await self.state_repo.find_by_state(state)
        if db_state:
            is_valid = db_state.expire_at > datetime.now()
            await self.state_repo.delete_by_state(state)
            return is_valid
        return False
