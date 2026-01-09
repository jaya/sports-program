from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.exceptions.business import DatabaseError, DuplicateEntityError
from app.models.user import User
from app.schemas.user_schema import UserCreate
from app.repositories.user_repository import UserRepository


class UserService:
    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
    ):
        self.user_repo = UserRepository(db)

    async def create(self, user: UserCreate):
        user_found = await self.user_repo.find_by_slack_id(user.slack_id)
        if user_found:
            raise DuplicateEntityError("User", "slack_id", user.slack_id)

        db_user = User(slack_id=user.slack_id, display_name=user.display_name)

        try:
            return await self.user_repo.create(db_user)
        except Exception as e:
            raise DatabaseError() from e

    async def find_all(self):
        return await self.user_repo.get_all()

    async def find_by_slack_id(self, slack_id: str):
        return await self.user_repo.find_by_slack_id(slack_id)
