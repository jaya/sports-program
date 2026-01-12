from fastapi import Depends

from app.services.program_service import ProgramService
from app.services.activity_service import ActivityService
from app.services.achievements.create_batch import CreateBatch
from app.schemas.achievement import AchievementBatchCreate, AchievementBatchResponse
from app.exceptions.business import EntityNotFoundError


class CloseCycle:
    def __init__(
        self,
        program_service: ProgramService = Depends(),
        activity_service: ActivityService = Depends(),
        create_batch: CreateBatch = Depends(),
    ):
        self.program_service = program_service
        self.activity_service = activity_service
        self.create_batch = create_batch

    async def execute(
        self, program_name: str, cycle_reference: str
    ) -> AchievementBatchResponse | None:
        program = await self.program_service.find_by_name(program_name)
        if not program:
            raise EntityNotFoundError("Program", program_name)

        user_ids = await self.activity_service.find_all_user_by_program_completed(
            program_name=program_name, cycle_reference=cycle_reference
        )

        if not user_ids:
            return None

        batch = AchievementBatchCreate(
            user_ids=user_ids,
            program_id=program.id,
            program_name=program.name,
            cycle_reference=cycle_reference,
        )

        return await self.create_batch.execute(batch)
