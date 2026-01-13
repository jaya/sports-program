from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.activity_schema import ActivityCreate
from app.schemas.program import ProgramCreate
from app.services.activity_service import ActivityService
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


async def register_activity_action(
    db: AsyncSession,
    slack_channel: str,
    slack_user_id: str,
    activity_create: ActivityCreate,
):
    service = ActivityService(db=db)
    return await service.create(
        program_slack_channel=slack_channel,
        slack_id=slack_user_id,
        activity_create=activity_create,
    )
