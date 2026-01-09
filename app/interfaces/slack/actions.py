from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.program import ProgramCreate
from app.services.programs.create import Create as CreateProgram
from app.services.programs.find_by_name_and_slack_channel import (
    FindByNameAndSlackChannel,
)


async def create_program_action(db: AsyncSession, name: str, slack_channel: str):
    start_date = datetime.now()
    end_date = start_date + timedelta(days=30)

    program_create = ProgramCreate(
        name=name,
        slack_channel=slack_channel,
        start_date=start_date,
        end_date=end_date,
    )

    repo = FindByNameAndSlackChannel(db=db)
    service = CreateProgram(db=db, program_find_by_name_slack_channel=repo)

    return await service.execute(program_create)
