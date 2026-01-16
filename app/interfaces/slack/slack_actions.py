from datetime import datetime, timedelta

from app.schemas.program_schema import ProgramCreate, ProgramResponse
from app.services.program_service import ProgramService


async def create_program_action(
    service: ProgramService, name: str, slack_channel: str
) -> ProgramResponse:
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
    return await service.find_all()
