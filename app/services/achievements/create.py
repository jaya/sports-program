from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.core.database import get_db
from app.schemas.achievement import AchievementCreate
from app.models.achievement import Achievement
from app.exceptions.business import DatabaseError


class Create:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def execute(
        self,
        achievement_create: AchievementCreate,
        program_id: int,
        user_id: int,
    ):
        db_achievement = Achievement(
            user_id=user_id,
            program_id=program_id,
            cycle_reference=achievement_create.cycle_reference,
        )
        self.db.add(db_achievement)
        try:
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError() from e
