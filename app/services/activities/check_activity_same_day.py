from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime

from app.core.database import get_db
from app.schemas.activity import Activity


class CheckActivitySameDay:
    def __init__(
        self, 
        db: AsyncSession = Depends(get_db),
    ):
        self.db = db


    async def execute(
        self,
        program_id: int,
        user_id: int,
        performed_at: datetime,
    ):
        activity_date = performed_at.date()
        stmt = select(Activity).where(
            Activity.user_id == user_id,
            Activity.program_id == program_id,
            func.date(Activity.performed_at) == activity_date
        )
        result = await self.db.execute(stmt)
        existing_activity = result.scalars().first()
        if existing_activity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"An activity is already registered for the user on this date ({activity_date})."
            )
    