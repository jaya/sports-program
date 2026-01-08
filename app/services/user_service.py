from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.exceptions.business import DatabaseError, DuplicateEntityError
from app.models.user import User
from app.schemas.user_schema import UserCreate


class UserService:
    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
    ):
        self.db = db

    async def create(self, user: UserCreate):
        user_found = await self.find_by_slack_id(user.slack_id)
        if user_found:
            raise DuplicateEntityError("User", "slack_id", user.slack_id)

        db_user = User(slack_id=user.slack_id, display_name=user.display_name)
        self.db.add(db_user)
        try:
            await self.db.commit()
            await self.db.refresh(db_user)
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError() from e

        return db_user

    async def find_all(self):
        stmt = select(User)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def find_by_slack_id(self, slack_id: str):
        stmt = select(User).where(User.slack_id == slack_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()
