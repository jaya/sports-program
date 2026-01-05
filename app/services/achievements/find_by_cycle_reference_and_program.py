from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import contains_eager

from app.core.database import get_db
from app.services.programs.find_by_slack_channel import FindBySlackChannel
from app.exceptions.business import EntityNotFoundError
from app.models.achievement import Achievement
from app.models.program import Program


class FindByCycleReferenceAndProgram:
    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
        program_find_by_slack_channel: FindBySlackChannel = Depends()
    ):
        self.db = db
        self.program_find_by_slack_channel = program_find_by_slack_channel

    async def execute(
        self,
        program_slack_channel: int,
        cycle_reference: str
    ) -> list[Achievement]:
        program_found = await self.program_find_by_slack_channel.execute(program_slack_channel)
        if not program_found:
            raise EntityNotFoundError("Program", program_slack_channel)

        stmt = (
            select(Achievement)
            .join(Achievement.user)
            .join(Achievement.program)
            .where(
                Program.slack_channel == program_slack_channel,
                Achievement.cycle_reference == cycle_reference
            )
            .options(
                contains_eager(Achievement.user),
                contains_eager(Achievement.program)
            )
        )

        result = await self.db.execute(stmt)
        return result.scalars().all()
