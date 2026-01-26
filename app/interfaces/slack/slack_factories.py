from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.achievement_repository import AchievementRepository
from app.repositories.activity_repository import ActivityRepository
from app.repositories.program_repository import ProgramRepository
from app.repositories.user_repository import UserRepository
from app.services.activity_service import ActivityService
from app.services.program_service import ProgramService
from app.services.user_service import UserService


def get_program_service(db: AsyncSession) -> ProgramService:
    repo = ProgramRepository(session=db)
    return ProgramService(program_repo=repo)


def get_activity_service(db: AsyncSession) -> ActivityService:
    user_repo = UserRepository(session=db)
    program_repo = ProgramRepository(session=db)
    activity_repo = ActivityRepository(session=db)
    achievement_repo = AchievementRepository(session=db)

    user_service = UserService(user_repo=user_repo)
    program_service = ProgramService(program_repo=program_repo)

    return ActivityService(
        db=db,
        user_service=user_service,
        program_service=program_service,
        activity_repo=activity_repo,
        achievement_repo=achievement_repo,
    )
