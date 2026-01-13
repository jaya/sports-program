from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.interfaces.slack.factories import get_activity_service, get_program_service
from app.schemas.activity_schema import ActivityCreate
from app.schemas.program_schema import ProgramCreate


async def create_program_action(db: AsyncSession, name: str, slack_channel: str):
    start_date = datetime.now()
    end_date = start_date + timedelta(days=30)

    program_create = ProgramCreate(
        name=name,
        slack_channel=slack_channel,
        start_date=start_date,
        end_date=end_date,
    )

    service = get_program_service(db)

    return await service.create(program_create)


async def register_activity_action(
    db: AsyncSession,
    slack_channel: str,
    slack_user_id: str,
    activity_create: ActivityCreate,
):
    service = get_activity_service(db)
    return await service.create(
        program_slack_channel=slack_channel,
        slack_id=slack_user_id,
        activity_create=activity_create,
    )
