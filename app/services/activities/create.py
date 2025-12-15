from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.activity import ActivityCreate
from app.schemas.activity import Activity
from app.models.user import UserCreate
from app.services.users.find_by_slack_id import FindBySlackId
from app.services.users.create import Create
from app.services.activities.check_activity_same_day import CheckActivitySameDay


class Create:
    def __init__(
        self, 
        db: AsyncSession = Depends(get_db),
        user_find_by_slack_id: FindBySlackId = Depends(),
        user_create: Create = Depends(),
        check_activity_same_day: CheckActivitySameDay = Depends()
    ):
        self.db = db
        self.user_find_by_slack_id = user_find_by_slack_id
        self.user_create = user_create
        self.check_activity_same_day = check_activity_same_day


    async def execute(
        self,
        activity_create: ActivityCreate,
        program_id: int,
        slack_id: str,
    ):
        user_id: int
        user_found = await self.user_find_by_slack_id.execute(slack_id)
        if user_found:
            user_id = user_found.id
        else:
            new_user = await self.user_create.execute(UserCreate(slack_id=slack_id, display_name=slack_id))
            user_id = new_user.id

        await self.check_activity_same_day.execute(
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
    