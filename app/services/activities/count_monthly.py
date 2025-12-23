from fastapi import Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.database import get_db
from app.models.activity import Activity


class CountActivitiesService:
    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
    ):
        self.db = db

    async def execute(self, user_id: int, performed_at: datetime) -> int:
        stmt = (
            select(func.count(Activity.id))
            .where(
                Activity.user_id == user_id,
                Activity.filter_date_tz(performed_at.year, performed_at.month)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0
