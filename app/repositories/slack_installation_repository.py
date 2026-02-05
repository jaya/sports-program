from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.slack_installation import SlackInstallation
from app.repositories.base_repository import BaseRepository


class SlackInstallationRepository(BaseRepository[SlackInstallation]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, SlackInstallation)

    async def find_by_team_id(self, team_id: str) -> SlackInstallation | None:
        stmt = select(SlackInstallation).where(SlackInstallation.team_id == team_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_org_wide_install(
        self, enterprise_id: str
    ) -> SlackInstallation | None:
        stmt = select(SlackInstallation).where(
            SlackInstallation.enterprise_id == enterprise_id,
            SlackInstallation.is_enterprise_install.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_team_or_enterprise(
        self, team_id: str | None, enterprise_id: str | None
    ) -> SlackInstallation | None:
        if not team_id and not enterprise_id:
            return None

        conditions = []
        if team_id:
            conditions.append(SlackInstallation.team_id == team_id)
        if enterprise_id:
            conditions.append(SlackInstallation.enterprise_id == enterprise_id)

        stmt = select(SlackInstallation).where(or_(*conditions))
        result = await self.session.execute(stmt)
        installations = result.scalars().all()

        if not installations:
            return None

        if len(installations) == 1:
            return installations[0]

        for inst in installations:
            if team_id and inst.team_id == team_id:
                return inst

        return installations[0]
