import logging
from datetime import datetime

from slack_sdk.oauth.installation_store import Installation
from slack_sdk.oauth.installation_store.async_installation_store import (
    AsyncInstallationStore,
)
from slack_sdk.oauth.state_store.async_state_store import AsyncOAuthStateStore
from sqlalchemy import select

from app.models.slack_installation import SlackInstallation, SlackState

logger = logging.getLogger(__name__)


class SQLAlchemyInstallationStore(AsyncInstallationStore):
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def async_save(self, installation: Installation):
        async with self.session_factory() as session:
            if installation.team_id:
                stmt = select(SlackInstallation).where(
                    SlackInstallation.team_id == installation.team_id
                )
            else:
                stmt = select(SlackInstallation).where(
                    SlackInstallation.enterprise_id == installation.enterprise_id,
                    SlackInstallation.is_enterprise_install.is_(True),
                )
            result = await session.execute(stmt)
            db_installation = result.scalar_one_or_none()

            if not db_installation:
                db_installation = SlackInstallation(
                    team_id=installation.team_id,
                    enterprise_id=installation.enterprise_id,
                    is_enterprise_install=installation.is_enterprise_install,
                )
                session.add(db_installation)

            db_installation.bot_token = installation.bot_token
            db_installation.bot_id = installation.bot_id
            db_installation.bot_user_id = installation.bot_user_id
            db_installation.installer_user_id = installation.user_id
            db_installation.scope = (
                ",".join(installation.bot_scopes) if installation.bot_scopes else None
            )

            await session.commit()

    def _row_to_installation(self, row: SlackInstallation) -> Installation:
        return Installation(
            app_id=None,
            enterprise_id=row.enterprise_id,
            team_id=row.team_id,
            bot_token=row.bot_token,
            bot_id=row.bot_id,
            bot_user_id=row.bot_user_id,
            bot_scopes=(row.scope.split(",") if row.scope else []),
            user_id=row.installer_user_id,
            is_enterprise_install=row.is_enterprise_install,
        )

    async def async_find_bot(
        self,
        *,
        enterprise_id: str | None,
        team_id: str | None,
        is_enterprise_install: bool | None = False,
    ) -> Installation | None:
        async with self.session_factory() as session:
            # 1. Search by team_id if provided
            if team_id:
                stmt = select(SlackInstallation).where(
                    SlackInstallation.team_id == team_id
                )
                result = await session.execute(stmt)
                db_installation = result.scalar_one_or_none()
                if db_installation:
                    return self._row_to_installation(db_installation)

            # 2. Search by enterprise_id (Org-wide install) if team search fails or team_id falls null
            if enterprise_id:
                stmt = select(SlackInstallation).where(
                    SlackInstallation.enterprise_id == enterprise_id,
                    SlackInstallation.is_enterprise_install.is_(True),
                )
                result = await session.execute(stmt)
                db_installation = result.scalar_one_or_none()
                if db_installation:
                    return self._row_to_installation(db_installation)

        return None


class SQLAlchemyStateStore(AsyncOAuthStateStore):
    def __init__(self, session_factory, expiration_seconds: int):
        self.session_factory = session_factory
        self.expiration_seconds = expiration_seconds

    async def async_issue(self, *args, **kwargs) -> str:
        import uuid

        state = str(uuid.uuid4())
        expire_at = datetime.fromtimestamp(
            datetime.now().timestamp() + self.expiration_seconds
        )

        async with self.session_factory() as session:
            db_state = SlackState(state=state, expire_at=expire_at)
            session.add(db_state)
            await session.commit()

        return state

    async def async_consume(self, state: str) -> bool:
        async with self.session_factory() as session:
            stmt = select(SlackState).where(SlackState.state == state)
            result = await session.execute(stmt)
            db_state = result.scalar_one_or_none()

            if db_state:
                if db_state.expire_at > datetime.now():
                    await session.delete(db_state)
                    await session.commit()
                    return True
                else:
                    await session.delete(db_state)
                    await session.commit()

        return False
