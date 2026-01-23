from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.repositories.base_repository import BaseRepository, logger


class UserRepository(BaseRepository[User]):
    def __init__(self, session: Annotated[AsyncSession, Depends(get_db)]):
        super().__init__(session, User)

    async def find_by_slack_id(self, slack_id: str) -> User | None:
        logger.debug("Searching for user by Slack ID", slack_id=slack_id)
        stmt = select(User).where(User.slack_id == slack_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def find_all_by_ids(self, user_ids: list[int]) -> list[User]:
        stmt = select(User).where(User.id.in_(user_ids))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
