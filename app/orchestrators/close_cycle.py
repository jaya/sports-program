import structlog
from typing import Annotated

from fastapi import Depends

from app.exceptions.business import EntityNotFoundError
from app.schemas.achievement import AchievementBatchCreate, AchievementBatchResponse
from app.services.achievement_service import AchievementService
from app.services.activity_service import ActivityService
from app.services.program_service import ProgramService

logger = structlog.get_logger()

class CloseCycle:
    def __init__(
        self,
        program_service: Annotated[ProgramService, Depends()],
        activity_service: Annotated[ActivityService, Depends()],
        achievement_service: Annotated[AchievementService, Depends()],
    ):
        self.program_service = program_service
        self.activity_service = activity_service
        self.achievement_service = achievement_service

    async def execute(
        self, program_name: str, cycle_reference: str
    ) -> AchievementBatchResponse | None:
        logger.info("close_cycle_started", program_name=program_name, cycle_reference=cycle_reference)
        
        program = await self.program_service.find_by_name(program_name)
        if not program:
            logger.warning("close_cycle_program_not_found", program_name=program_name)
            raise EntityNotFoundError("Program", program_name)

        user_ids = await self.activity_service.find_all_user_by_program_completed(
            program_name=program_name, cycle_reference=cycle_reference
        )

        if not user_ids:
            logger.info("close_cycle_no_users", program_name=program_name, cycle_reference=cycle_reference)
            return None

        logger.info("close_cycle_users_found", count=len(user_ids), program_name=program_name)

        batch = AchievementBatchCreate(
            user_ids=user_ids,
            program_id=program.id,
            program_name=program.name,
            cycle_reference=cycle_reference,
        )

        result = await self.achievement_service.create_batch(batch)
        logger.info("close_cycle_finished", program_name=program_name, cycle_reference=cycle_reference)
        return result
