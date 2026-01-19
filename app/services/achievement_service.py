import structlog
from typing import Annotated

from fastapi import Depends

from app.exceptions.business import DatabaseError
from app.models.achievement import Achievement
from app.repositories.achievement_repository import AchievementRepository
from app.repositories.user_repository import UserRepository
from app.schemas.achievement import (
    AchievementBatchCreate,
    AchievementBatchResponse,
    AchievementCreate,
)

logger = structlog.get_logger()

class AchievementService:
    def __init__(
        self,
        achievement_repo: Annotated[AchievementRepository, Depends()],
        user_repo: Annotated[UserRepository, Depends()],
    ):
        self.achievement_repo = achievement_repo
        self.user_repo = user_repo

    async def create(
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
        try:
            return await self.achievement_repo.create(db_achievement)
        except Exception as e:
            raise DatabaseError() from e

    async def create_batch(
        self, achievement_batch: AchievementBatchCreate
    ) -> AchievementBatchResponse:
        logger.info("achievement_batch_started", program_id=achievement_batch.program_id, cycle=achievement_batch.cycle_reference)
        existing_user_ids = await self.achievement_repo.find_existing_user_ids(
            program_id=achievement_batch.program_id,
            cycle_reference=achievement_batch.cycle_reference,
            user_ids=achievement_batch.user_ids,
        )

        if existing_user_ids:
            logger.info("achievements_skipped", count=len(existing_user_ids))

        new_user_ids = [
            uid for uid in achievement_batch.user_ids if uid not in existing_user_ids
        ]

        if new_user_ids:
            db_achievements = [
                Achievement(
                    user_id=user_id,
                    program_id=achievement_batch.program_id,
                    cycle_reference=achievement_batch.cycle_reference,
                )
                for user_id in new_user_ids
            ]
            try:
                await self.achievement_repo.create_many(db_achievements)
                logger.info("achievement_created", count=len(new_user_ids))
            except Exception as e:
                logger.error("entity_creation_failed", entity="Achievement", error=str(e))
                raise DatabaseError() from e

        users = []
        if new_user_ids:
            users = await self.user_repo.find_all_by_ids(new_user_ids)

        logger.info("achievement_batch_completed", total=len(new_user_ids))
        return AchievementBatchResponse(
            total_created=len(new_user_ids),
            program_name=achievement_batch.program_name,
            cycle_reference=achievement_batch.cycle_reference,
            users=[str(user.display_name) for user in users],
        )
