from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
from typing import Optional

from app.exceptions.business import BusinessRuleViolationError
from app.core.database import get_db
from app.models.activity import Activity


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
        exclude_id: Optional[int] = None
    ):
        activity_date = performed_at.date()
        stmt = select(Activity).where(
            Activity.user_id == user_id,
            Activity.program_id == program_id,
            func.date(Activity.performed_at) == activity_date
        )
        if exclude_id is not None:
            stmt = stmt.where(Activity.id != exclude_id)
        result = await self.db.execute(stmt)
        existing_activity = result.scalars().first()
        if existing_activity:
            raise BusinessRuleViolationError(
                f"An activity is already registered for the user on this date ({activity_date}).")
