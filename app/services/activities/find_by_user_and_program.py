from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager
from sqlalchemy import select

from app.exceptions.business import EntityNotFoundError
from app.core.database import get_db
from app.models.activity import Activity
from app.models.program import Program
from app.services.users.find_by_slack_id import FindBySlackId
from app.services.programs.find_by_slack_channel import FindBySlackChannel
from app.services.utils.reference_date import ReferenceDate


class FindByUserAndProgram:
    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
        user_find_by_slack_id: FindBySlackId = Depends(),
        program_find_by_slack_channel: FindBySlackChannel = Depends()
    ):
        self.db = db
        self.user_find_by_slack_id = user_find_by_slack_id
        self.program_find_by_slack_channel = program_find_by_slack_channel

    async def execute(
        self,
        program_slack_channel: int,
        slack_id: str,
        reference_date: str
    ):
        user_found = await self.user_find_by_slack_id.execute(slack_id)
        if not user_found:
            raise EntityNotFoundError("User", slack_id)

        program_found = await self.program_find_by_slack_channel.execute(program_slack_channel)
        if not program_found:
            raise EntityNotFoundError("Program", program_slack_channel)

        ref = ReferenceDate.from_str(reference_date)

        stmt = (
            select(Activity)
            .join(Activity.user)
            .join(Activity.program)
            .where(
                Activity.user_id == user_found.id,
                Program.slack_channel == program_slack_channel,
                Activity.filter_date_tz(ref.year, ref.month)
            )
            .options(
                contains_eager(Activity.user),
                contains_eager(Activity.program)
            )
        )

        result = await self.db.execute(stmt)
        return result.scalars().all()
