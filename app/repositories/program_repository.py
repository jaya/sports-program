
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.program import Program
from app.repositories.base_repository import BaseRepository


class ProgramRepository(BaseRepository[Program]):
    def __init__(self, session: AsyncSession = Depends(get_db)):
        super().__init__(session, Program)

    async def find_by_name(self, name: str) -> Program | None:
        stmt = select(Program).where(Program.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_name_and_slack_channel(self, name: str, slack_channel: str) -> Program | None:
        stmt = select(Program).where(
            Program.name == name,
            Program.slack_channel == slack_channel
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_slack_channel(self, slack_channel: str) -> list[Program]:
        stmt = select(Program).where(Program.slack_channel == slack_channel)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
