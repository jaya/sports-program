from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.program import ProgramCreate
from app.services.program_service import ProgramService
from app.repositories.program_repository import ProgramRepository


async def create_program_action(db: AsyncSession, name: str, slack_channel: str):
    start_date = datetime.now()
    end_date = start_date + timedelta(days=30)

    program_create = ProgramCreate(
        name=name,
        slack_channel=slack_channel,
        start_date=start_date,
        end_date=end_date,
    )

    repo = ProgramRepository(session=db)
    service = ProgramService(program_repo=repo)

    return await service.create(program_create)
