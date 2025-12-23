from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.business import DuplicateEntityError, DatabaseError
from app.schemas.user import UserCreate
from app.models.user import User
from app.core.database import get_db
from app.services.users.find_by_slack_id import FindBySlackId


class Create:
    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
        user_find_by_slack_id: FindBySlackId = Depends()
    ):
        self.db = db
        self.user_find_by_slack_id = user_find_by_slack_id

    async def execute(self, user: UserCreate):
        user_found = await self.user_find_by_slack_id.execute(user.slack_id)
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
