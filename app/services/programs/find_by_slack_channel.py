from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.program import Program
from app.core.database import get_db


class FindBySlackChannel:
    def __init__(
            self,
            db: AsyncSession = Depends(get_db)
    ):
        self.db = db

    async def execute(self, slack_channel: str):
        stmt = select(Program).where(Program.slack_channel == slack_channel)
        result = await self.db.execute(stmt)
        return result.scalars().all()
