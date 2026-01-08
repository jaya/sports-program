from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager

from app.core.database import get_db
from app.exceptions.business import EntityNotFoundError
from app.models.achievement import Achievement
from app.services.programs.find_by_name import FindByName
from app.services.user_service import UserService
from app.services.utils.reference_date import ReferenceDate


class FindByUser:
    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
        user_service: UserService = Depends(),
        program_find_by_name: FindByName = Depends(),
    ):
        self.db = db
        self.user_service = user_service
        self.program_find_by_name = program_find_by_name

    async def execute(self, slack_id: str, program_name: str, reference_date: str):
        user_found = await self.user_service.find_by_slack_id(slack_id)
        if not user_found:
            raise EntityNotFoundError("User", slack_id)

        program_found = await self.program_find_by_name.execute(program_name)
        if not program_found:
            raise EntityNotFoundError("Program", program_name)

        ref = ReferenceDate.from_str(reference_date)

        stmt = (
            select(Achievement)
            .join(Achievement.user)
            .join(Achievement.program)
            .where(
                Achievement.user_id == user_found.id,
                Achievement.program_id == program_found.id,
                Achievement.cycle_reference == ref,
            )
            .options(
                contains_eager(Achievement.user), contains_eager(Achievement.program)
            )
        )

        result = await self.db.execute(stmt)
        return result.scalars().all()
