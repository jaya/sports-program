from typing import Annotated

from calendar import monthrange
from datetime import datetime, timezone

from fastapi import Depends
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.program import Program
from app.repositories.base_repository import BaseRepository


class ProgramRepository(BaseRepository[Program]):
    def __init__(self, session: Annotated[AsyncSession, Depends(get_db)]):
        super().__init__(session, Program)

    async def find_by_name(self, name: str) -> Program | None:
        stmt = select(Program).where(Program.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_name_and_slack_channel(
            self,
            name: str,
            slack_channel: str
    ) -> Program | None:
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

    async def find_active_in_cycle(self, cycle_reference: str) -> list[Program]:
        year, month = map(int, cycle_reference.split("-"))
        last_day = monthrange(year, month)[1]

        cycle_start = datetime(year, month, 1, 0, 0, 0, tzinfo=timezone.utc)
        cycle_end = datetime(year, month, last_day, 23,
                             59, 59, tzinfo=timezone.utc)

        stmt = select(Program).where(
            Program.start_date <= cycle_end,
            or_(
                Program.end_date.is_(None),
                Program.end_date >= cycle_start
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
