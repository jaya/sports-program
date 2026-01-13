from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi import Depends

from app.core.database import get_db
from app.models.achievement import Achievement
from app.models.user import User
from app.schemas.achievement import AchievementBatchCreate, AchievementBatchResponse
from app.exceptions.business import DatabaseError, DuplicateEntityError


class CreateBatch:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def execute(
        self,
        achievement_batch: AchievementBatchCreate
    ) -> AchievementBatchResponse:
        users = await self._get_users(achievement_batch.user_ids)
        user_names = [user.display_name for user in users]

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
        except IntegrityError as e:
            await self.db.rollback()
            raise DuplicateEntityError(
                entity="Achievement",
                field="program/cycle_reference",
                value=f"{achievement_batch.program_name}/{achievement_batch.cycle_reference}"
            ) from e
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError() from e

        return AchievementBatchResponse(
            total_created=len(db_achievements),
            program_name=achievement_batch.program_name,
            cycle_reference=achievement_batch.cycle_reference,
            users=user_names,
        )

    async def _get_users(self, user_ids: list[int]) -> list[User]:
        stmt = select(User).where(User.id.in_(user_ids))
        result = await self.db.execute(stmt)
        return result.scalars().all()
