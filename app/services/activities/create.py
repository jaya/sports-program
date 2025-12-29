from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.exceptions.business import BusinessRuleViolationError, EntityNotFoundError, DatabaseError
from app.core.database import get_db
from app.models.activity import Activity
from app.schemas.activity import ActivityCreate, ActivitySummaryResponse
from app.schemas.user import UserCreate
from app.services.users.find_by_slack_id import FindBySlackId
from app.services.users.create import Create
from app.services.activities.check_activity_same_day import CheckActivitySameDay
from app.services.programs.find_by_slack_channel import FindBySlackChannel
from app.services.activities.count_monthly import CountActivitiesService


class Create:
    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
        user_find_by_slack_id: FindBySlackId = Depends(),
        user_create: Create = Depends(),
        check_activity_same_day: CheckActivitySameDay = Depends(),
        program_find_by_slack_channel: FindBySlackChannel = Depends(),
        count_service: CountActivitiesService = Depends()
    ):
        self.db = db
        self.user_find_by_slack_id = user_find_by_slack_id
        self.user_create = user_create
        self.check_activity_same_day = check_activity_same_day
        self.program_find_by_slack_channel = program_find_by_slack_channel
        self.count_service = count_service

    async def execute(
        self,
        activity_create: ActivityCreate,
        program_slack_channel: str,
        slack_id: str,
    ):
        # TODO: Fix more than one program with same slack channel
        user_id = await self.validate_user(slack_id)
        program_found = await self.validate_program(program_slack_channel)
        performed_at = self.validate_performed_at(
            program_found,
            activity_create.performed_at
        )
        await self.check_activity_same_day.execute(
            program_found.id,
            user_id,
            performed_at
        )

        db_activity = Activity(
            user_id=user_id,
            program_id=program_found.id,
            description=activity_create.description,
            evidence_url=activity_create.evidence_url,
            performed_at=performed_at
        )
        self.db.add(db_activity)
        try:
            await self.db.commit()
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
        if user_found:
            return user_found.id
        else:
            new_user = await self.user_create.execute(UserCreate(slack_id=slack_id, display_name=slack_id))
            return new_user.id

    async def validate_program(self, program_slack_channel):
        program_found = await self.program_find_by_slack_channel.execute(program_slack_channel)
        if not program_found:
            raise EntityNotFoundError("Program", program_slack_channel)

        if len(program_found) > 1:
            raise BusinessRuleViolationError(
                f"There are {len(program_found)} programs linked to the channel '{program_slack_channel}'. "
                "It is not possible to determine in which one to register the activity automatically."
            )

        return program_found[0]

    def validate_performed_at(self, program_found, performed_at):
        if not performed_at:
            performed_at = datetime.now()
        if performed_at > datetime.now():
            raise BusinessRuleViolationError(
                "Activity date cannot be in the future")

        # Garante que performed_at e program_found.start_date sejam comparáveis
        start_date = program_found.start_date
        if performed_at.tzinfo is None and start_date.tzinfo is not None:
            performed_at = performed_at.replace(tzinfo=start_date.tzinfo)
        elif performed_at.tzinfo is not None and start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=performed_at.tzinfo)

        if performed_at < start_date:
            raise BusinessRuleViolationError(
                "Activity date is outside the program date range")

        if program_found.end_date:
            end_date = program_found.end_date
            # Garante a mesma consistência para a data de fim
            if performed_at.tzinfo is None and end_date.tzinfo is not None:
                performed_at = performed_at.replace(tzinfo=end_date.tzinfo)
            elif performed_at.tzinfo is not None and end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=performed_at.tzinfo)

            if performed_at > end_date:
                raise BusinessRuleViolationError(
                    "Activity date is outside the program date range")
                return performed_at
