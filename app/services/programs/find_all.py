from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.program import Program
from app.core.database import get_db


class FindAll:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def execute(self):
        stmt = select(Program)
        result = await self.db.execute(stmt)
        return result.scalars().all()
