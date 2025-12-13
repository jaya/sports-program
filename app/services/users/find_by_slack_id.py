from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.user import User
from app.core.database import get_db


class FindBySlackId:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def execute(self, slack_id: str):
        stmt = select(User).where(User.slack_id == slack_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()