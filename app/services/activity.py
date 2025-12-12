from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime

from app.core.database import get_db
from app.models.activity import ActivityCreate
from app.schemas.activity import Activity
from app.models.user import UserCreate
from app.services.user import UserService


class ActivityService:
    def __init__(
        self, 
        db: AsyncSession = Depends(get_db),
        user_service: UserService = Depends()
    ):
        self.db = db
        self.user_service = user_service


    async def find_activities_by_user(self, slack_id: str):
        user_found = await self.user_service.find_user_by_slack_id(slack_id)
        if not user_found:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with this slack_id not found")
        stmt = select(Activity).where(Activity.user_id == user_found.id)
        result = await self.db.execute(stmt)
        activities = result.scalars().all()
        return activities


    async def find_activities_by_user_and_program(
        self,
        program_id: int,
        slack_id: str,
    ):
        user_found = await self.user_service.find_user_by_slack_id(slack_id)
        if not user_found:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with this slack_id not found")
        stmt = select(Activity).where(Activity.user_id == user_found.id, Activity.program_id == program_id)
        result = await self.db.execute(stmt)
        activities = result.scalars().all()
        return activities


    async def insert_activity(
        self,
        activity_create: ActivityCreate,
        program_id: int,
        slack_id: str,
    ):
        user_id: int
        user_found = await self.user_service.find_user_by_slack_id(slack_id)
        if user_found:
            user_id = user_found.id
        else:
            new_user = await self.user_service.insert_new_user(UserCreate(slack_id=slack_id, display_name=slack_id))
            user_id = new_user.id

        await self.check_activity_the_same_day(
            program_id, 
            user_id,
            activity_create.performed_at
        )

        db_activity = Activity(
            user_id=user_id,
            program_id=program_id,
            description=activity_create.description,
            evidence_url=activity_create.evidence_url,
            performed_at=activity_create.performed_at
        )
        self.db.add(db_activity)
        try:
            await self.db.commit()
            await self.db.refresh(db_activity)
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"An error occurred: {str(e)}"
            )
        
        return db_activity


    async def check_activity_the_same_day(
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
    