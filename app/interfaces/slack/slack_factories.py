from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.program_repository import ProgramRepository
from app.services.program_service import ProgramService


def get_program_service(db: AsyncSession) -> ProgramService:
    repo = ProgramRepository(session=db)
    return ProgramService(program_repo=repo)
