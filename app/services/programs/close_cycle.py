from fastapi import Depends

from app.services.activities.find_all_user_by_program_completed import FindAllUserByProgramCompleted
from app.services.achievements.create_batch import CreateBatch
from app.services.programs.find_by_name import FindByName
from app.schemas.achievement import AchievementBatchCreate, AchievementBatchResponse
from app.exceptions.business import EntityNotFoundError


class CloseCycle:
    def __init__(
        self,
        find_completed: FindAllUserByProgramCompleted = Depends(),
        create_batch: CreateBatch = Depends(),
        find_program: FindByName = Depends()
    ):
        self.find_completed = find_completed
        self.create_batch = create_batch
        self.find_program = find_program

    async def execute(
        self,
        program_name: str,
        cycle_reference: str
    ) -> AchievementBatchResponse | None:
        program = await self.find_program.execute(program_name)
        if not program:
            raise EntityNotFoundError("Program", program_name)

        user_ids = await self.find_completed.execute(
            program_name=program_name,
            cycle_reference=cycle_reference
        )

        if not user_ids:
            return None

        batch = AchievementBatchCreate(
            user_ids=user_ids,
            program_id=program.id,
            cycle_reference=cycle_reference
        )

        return await self.create_batch.execute(batch)
