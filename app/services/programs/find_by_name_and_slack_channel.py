from datetime import datetime, timezone
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.models.program import Program
from app.core.database import get_db


class FindByNameAndSlackChannel:
    def __init__(
            self,
            db: AsyncSession = Depends(get_db)
    ):
        self.db = db

    async def execute(self, name: str, slack_channel: str):
        now = datetime.now(timezone.utc)
        stmt = select(Program).where(
            Program.name == name,
            Program.slack_channel == slack_channel,
            or_(
                Program.end_date == None,
                Program.end_date >= now
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()
