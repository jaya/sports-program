from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.program import Program
from app.core.database import get_db


class FindById:
    def __init__(
            self,
            db: AsyncSession = Depends(get_db)
    ):
        self.db = db

    async def execute(self, id: str):
        stmt = select(Program).where(Program.id == id)
        result = await self.db.execute(stmt)
        return result.scalars().first()
