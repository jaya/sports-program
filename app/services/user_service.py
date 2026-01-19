import structlog
from fastapi import Depends

from app.exceptions.business import DatabaseError, DuplicateEntityError
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserCreate

logger = structlog.get_logger()

class UserService:
    def __init__(
        self,
        user_repo: UserRepository = Depends(),
    ):
        self.user_repo = user_repo

    async def create(self, user: UserCreate):
        user_found = await self.user_repo.find_by_slack_id(user.slack_id)
        if user_found:
            logger.warning("duplicate_entity", entity="User", slack_id=user.slack_id)
            raise DuplicateEntityError("User", "slack_id", user.slack_id)

        db_user = User(slack_id=user.slack_id, display_name=user.display_name)

        try:
            created = await self.user_repo.create(db_user)
            logger.info("user_created", slack_id=user.slack_id, display_name=user.display_name)
            return created
        except Exception as e:
            logger.error("entity_creation_failed", entity="User", error=str(e))
            raise DatabaseError() from e

    async def find_all(self):
        return await self.user_repo.get_all()

    async def find_by_slack_id(self, slack_id: str):
        return await self.user_repo.find_by_slack_id(slack_id)
