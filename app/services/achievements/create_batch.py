from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends

from app.core.database import get_db
from app.models.achievement import Achievement
from app.models.user import User
from app.models.program import Program
from app.schemas.achievement import AchievementBatchCreate, AchievementBatchResponse
from app.exceptions.business import DatabaseError


class CreateBatch:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def execute(
        self,
        achievement_batch: AchievementBatchCreate
    ) -> AchievementBatchResponse:
        db_achievements = [
            Achievement(
                user_id=user_id,
                program_id=achievement_batch.program_id,
                cycle_reference=achievement_batch.cycle_reference,
            )
            for user_id in achievement_batch.user_ids
        ]
        self.db.add_all(db_achievements)
        try:
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError() from e

        program = await self._get_program(achievement_batch.program_id)
        users = await self._get_users(achievement_batch.user_ids)

        return AchievementBatchResponse(
            total_created=len(db_achievements),
            program_name=program.name,
            cycle_reference=achievement_batch.cycle_reference,
            users=[user.display_name for user in users],
        )

    async def _get_program(self, program_id: int) -> Program:
        stmt = select(Program).where(Program.id == program_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def _get_users(self, user_ids: list[int]) -> list[User]:
        stmt = select(User).where(User.id.in_(user_ids))
        result = await self.db.execute(stmt)
        return result.scalars().all()
