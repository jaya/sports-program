from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import Depends

from app.core.database import get_db
from app.models.activity import Activity
from app.services.programs.find_by_name import FindByName
from app.services.utils.reference_date import ReferenceDate
from app.exceptions.business import EntityNotFoundError

GOAL_ACTIVITIES = 12


class FindAllUserByProgramCompleted:
    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
        program_find_by_name: FindByName = Depends()
    ):
        self.db = db
        self.program_find_by_name = program_find_by_name

    async def execute(
        self,
        program_name: str,
        cycle_reference: str
    ) -> list[int]:
        program_found = await self.program_find_by_name.execute(program_name)
        if not program_found:
            raise EntityNotFoundError("Program", program_name)

        ref = ReferenceDate.from_str(cycle_reference)

        stmt = (
            select(Activity.user_id)
            .where(
                Activity.program_id == program_found.id,
                Activity.filter_date_tz(ref.year, ref.month)
            )
            .group_by(Activity.user_id)
            .having(func.count(Activity.id) >= GOAL_ACTIVITIES)
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())
