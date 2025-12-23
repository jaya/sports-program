from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager
from sqlalchemy import select

from app.exceptions.business import EntityNotFoundError
from app.core.database import get_db
from app.models.activity import Activity
from app.models.user import User


class FindById:
    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
    ):
        self.db = db

    async def execute(self, id: int, slack_id: str):
        stmt = (
            select(Activity)
            .join(Activity.user)
            .join(Activity.program)
            .where(
                Activity.id == id,
                User.slack_id == slack_id
            )
            .options(
                contains_eager(Activity.user),
                contains_eager(Activity.program)
            )
        )

        result = await self.db.execute(stmt)
        db_activity = result.scalar_one_or_none()
        if not db_activity:
            raise EntityNotFoundError("Activity", id)
        return db_activity
