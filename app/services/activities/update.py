from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.exceptions.business import BusinessRuleViolationError, EntityNotFoundError, DatabaseError
from app.core.database import get_db
from app.schemas.activity import ActivityUpdate, ActivitySummaryResponse
from app.services.activities.count_monthly import CountActivitiesService
from app.services.activities.check_activity_same_day import CheckActivitySameDay
from app.services.activities.find_by_id import FindById
from app.services.programs.find_by_id import FindById as ProgramFindById
from app.services.users.find_by_slack_id import FindBySlackId


class Update:
    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
        user_find_by_slack_id: FindBySlackId = Depends(),
        check_activity_same_day: CheckActivitySameDay = Depends(),
        program_find_by_id: ProgramFindById = Depends(),
        count_service: CountActivitiesService = Depends(),
        find_by_id: FindById = Depends(),
    ):
        self.db = db
        self.user_find_by_slack_id = user_find_by_slack_id
        self.check_activity_same_day = check_activity_same_day
        self.program_find_by_id = program_find_by_id
        self.count_service = count_service
        self.find_by_id = find_by_id

    async def execute(
        self,
        activity_update: ActivityUpdate,
        id: int,
        slack_id: str,
    ):
        user_id = await self.validate_user(slack_id)
        db_activity = await self.find_by_id.execute(id, slack_id)
        program_found = await self.validate_program(db_activity.program_id)

        if activity_update.performed_at is not None and activity_update.performed_at != db_activity.performed_at:
            self.validate_performed_at(
                program_found,
                activity_update.performed_at
            )
            await self.check_activity_same_day.execute(
                program_found.id,
                user_id,
                activity_update.performed_at,
                id
            )

        update_data = activity_update.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(db_activity, key, value)

        self.db.add(db_activity)

        try:
            await self.db.commit()
            await self.db.refresh(db_activity)
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError() from e

        total_month = await self.count_service.execute(
            user_id=user_id,
            performed_at=db_activity.performed_at
        )

        return ActivitySummaryResponse(
            id=db_activity.id,
            count_month=total_month
        )

    async def validate_user(self, slack_id):
        user_found = await self.user_find_by_slack_id.execute(slack_id)
        if not user_found:
            raise EntityNotFoundError("User", slack_id)
        return user_found.id

    async def validate_program(self, program_id):
        program_found = await self.program_find_by_id.execute(program_id)
        if not program_found:
            raise EntityNotFoundError("Program", program_id)
        return program_found

    def validate_performed_at(self, program_found, performed_at):
        if performed_at > datetime.now():
            raise BusinessRuleViolationError(
                "Activity date cannot be in the future")

        if performed_at < program_found.start_date:
            raise BusinessRuleViolationError(
                "Activity date is outside the program date range")

        if program_found.end_date and performed_at > program_found.end_date:
            raise BusinessRuleViolationError(
                "Activity date is outside the program date range")
