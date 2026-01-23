import structlog
from datetime import datetime, timedelta

from app.schemas.activity_schema import ActivityCreate
from app.schemas.program_schema import ProgramCreate, ProgramResponse
from app.services.activity_service import ActivityService
from app.services.program_service import ProgramService

logger = structlog.get_logger()


async def create_program_action(
    service: ProgramService, name: str, slack_channel: str
) -> ProgramResponse:
    logger.info("Slack interactive action received", action="create_program", name=name, slack_channel=slack_channel)
    start_date = datetime.now()
    end_date = start_date + timedelta(days=30)

    program_create = ProgramCreate(
        name=name,
        slack_channel=slack_channel,
        start_date=start_date,
        end_date=end_date,
    )

    return await service.create(program_create)


async def list_programs_action(service: ProgramService) -> list[ProgramResponse]:
    logger.info("Slack interactive action received", action="list_programs")
    return await service.find_all()


async def list_activities_action(
    service: ActivityService,
    channel_id: str,
    slack_user_id: str,
    reference_date: str | None = None,
):
    logger.info("Slack interactive action received", action="list_activities", channel_id=channel_id, slack_user_id=slack_user_id, reference_date=reference_date)
    if not reference_date:
        reference_date = datetime.now().strftime("%Y-%m")
    return await service.find_by_user_and_program(
        program_slack_channel=channel_id,
        slack_id=slack_user_id,
        reference_date=reference_date,
    )


async def register_activity_action(
    service: ActivityService,
    slack_channel: str,
    slack_user_id: str,
    activity_create: ActivityCreate,
):
    logger.info("Slack interactive action received", action="register_activity", slack_channel=slack_channel, slack_user_id=slack_user_id)
    return await service.create(
        program_slack_channel=slack_channel,
        slack_id=slack_user_id,
        activity_create=activity_create,
    )
