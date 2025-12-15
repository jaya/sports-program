from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.program import Program
from app.core.database import get_db


class FindByName:
    def __init__(
            self,
            db: AsyncSession = Depends(get_db)
    ):
        self.db = db

    async def execute(self, name: str):
        stmt = select(Program).where(Program.name == name)
        result = await self.db.execute(stmt)
        return result.scalars().first()
