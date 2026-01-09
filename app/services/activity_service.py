from datetime import datetime
from typing import List, Optional

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.exceptions.business import (
    BusinessRuleViolationError,
    DatabaseError,
    EntityNotFoundError,
)
from app.models.activity import Activity
from app.schemas.activity import (
    ActivityCreate,
    ActivitySummaryResponse,
    ActivityUpdate,
)
from app.schemas.user_schema import UserCreate
from app.repositories.activity_repository import ActivityRepository
from app.services.user_service import UserService
from app.services.programs.find_by_slack_channel import FindBySlackChannel
from app.services.programs.find_by_id import FindById as ProgramFindById
from app.services.programs.find_by_name import FindByName as ProgramFindByName
from app.services.utils.reference_date import ReferenceDate
from app.utils.date_validator import is_within_allowed_window

GOAL_ACTIVITIES = 12


class ActivityService:
    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
        user_service: UserService = Depends(),
        program_find_by_slack_channel: FindBySlackChannel = Depends(),
        program_find_by_id: ProgramFindById = Depends(),
        program_find_by_name: ProgramFindByName = Depends(),
    ):
        self.db = db
        self.user_service = user_service
        self.program_find_by_slack_channel = program_find_by_slack_channel
        self.program_find_by_id = program_find_by_id
        self.program_find_by_name = program_find_by_name
        self.activity_repo = ActivityRepository(db)

    async def create(
        self,
        activity_create: ActivityCreate,
        program_slack_channel: str,
        slack_id: str,
    ) -> ActivitySummaryResponse:
        user_id = await self._validate_user(slack_id)
        program_found = await self._validate_program_by_slack_channel(
            program_slack_channel
        )
        performed_at = self._validate_performed_at(
            program_found, activity_create.performed_at
        )

        existing_activity = await self.activity_repo.check_activity_same_day(
            program_found.id, user_id, performed_at.date()
        )
        if existing_activity:
            raise BusinessRuleViolationError(
                f"An activity is already registered for the user on this date ({performed_at.date()})."
            )

        db_activity = Activity(
            user_id=user_id,
            program_id=program_found.id,
            description=activity_create.description,
            evidence_url=activity_create.evidence_url,
            performed_at=performed_at,
        )

        try:
            await self.activity_repo.create(db_activity)
        except Exception as e:
            raise DatabaseError() from e

        total_month = await self.activity_repo.count_monthly(
            user_id=user_id,
            year=db_activity.performed_at.year,
            month=db_activity.performed_at.month,
        )

        return ActivitySummaryResponse(id=db_activity.id, count_month=total_month)

    async def update(
        self,
        activity_update: ActivityUpdate,
        id: int,
        slack_id: str,
    ) -> ActivitySummaryResponse:
        user_found = await self.user_service.find_by_slack_id(slack_id)
        if not user_found:
            raise EntityNotFoundError("User", slack_id)
        user_id = user_found.id

        db_activity = await self.activity_repo.find_by_id_and_slack_id(id, slack_id)
        if not db_activity:
            raise EntityNotFoundError("Activity", id)

        program_found = await self.program_find_by_id.execute(db_activity.program_id)
        if not program_found:
            raise EntityNotFoundError("Program", db_activity.program_id)

        if (
            activity_update.performed_at is not None
            and activity_update.performed_at != db_activity.performed_at
        ):
            self._validate_performed_at(program_found, activity_update.performed_at)
            existing_activity = await self.activity_repo.check_activity_same_day(
                program_found.id, user_id, activity_update.performed_at.date(), id
            )
            if existing_activity:
                raise BusinessRuleViolationError(
                    f"An activity is already registered for the user on this date ({activity_update.performed_at.date()})."
                )

        update_data = activity_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_activity, key, value)

        try:
            await self.db.commit()
            await self.db.refresh(db_activity)
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError() from e

        total_month = await self.activity_repo.count_monthly(
            user_id=user_id,
            year=db_activity.performed_at.year,
            month=db_activity.performed_at.month,
        )

        return ActivitySummaryResponse(id=db_activity.id, count_month=total_month)

    async def delete(self, id: int, slack_id: str) -> None:
        activity = await self.activity_repo.find_by_id_and_slack_id(id, slack_id)
        if not activity:
            raise EntityNotFoundError("Activity", id)

        if not is_within_allowed_window(activity.performed_at):
            raise BusinessRuleViolationError(
                "Activities can only be deleted within the current or previous month."
            )

        try:
            await self.db.delete(activity)
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError() from e

    async def find_by_id(self, id: int, slack_id: str) -> Activity:
        activity = await self.activity_repo.find_by_id_and_slack_id(id, slack_id)
        if not activity:
            raise EntityNotFoundError("Activity", id)
        return activity

    async def find_by_user(self, slack_id: str, reference_date: str) -> List[Activity]:
        user_found = await self.user_service.find_by_slack_id(slack_id)
        if not user_found:
            raise EntityNotFoundError("User", slack_id)

        ref = ReferenceDate.from_str(reference_date)
        return await self.activity_repo.find_by_user_id_and_date(
            user_found.id, ref.year, ref.month
        )

    async def find_by_user_and_program(
        self, program_slack_channel: str, slack_id: str, reference_date: str
    ) -> List[Activity]:
        user_found = await self.user_service.find_by_slack_id(slack_id)
        if not user_found:
            raise EntityNotFoundError("User", slack_id)

        ref = ReferenceDate.from_str(reference_date)
        return await self.activity_repo.find_by_user_id_and_slack_channel_and_date(
            user_found.id, program_slack_channel, ref.year, ref.month
        )

    async def find_all_user_by_program_completed(
        self, program_name: str, cycle_reference: str
    ) -> List[int]:
        program_found = await self.program_find_by_name.execute(program_name)
        if not program_found:
            raise EntityNotFoundError("Program", program_name)

        ref = ReferenceDate.from_str(cycle_reference)
        return await self.activity_repo.find_users_with_completed_program(
            program_found.id, ref.year, ref.month, GOAL_ACTIVITIES
        )

    async def _validate_user(self, slack_id: str) -> int:
        user_found = await self.user_service.find_by_slack_id(slack_id)
        if user_found:
            return user_found.id
        else:
            new_user = await self.user_service.create(
                UserCreate(slack_id=slack_id, display_name=slack_id)
            )
            return new_user.id

    async def _validate_program_by_slack_channel(self, program_slack_channel: str):
        program_found = await self.program_find_by_slack_channel.execute(
            program_slack_channel
        )
        if not program_found:
            raise EntityNotFoundError("Program", program_slack_channel)

        if len(program_found) > 1:
            raise BusinessRuleViolationError(
                f"There are {len(program_found)} programs linked to the channel '{program_slack_channel}'. "
                "It is not possible to determine in which one to register the activity automatically."
            )

        return program_found[0]

    def _validate_performed_at(
        self, program_found, performed_at: Optional[datetime]
    ) -> datetime:
        if not performed_at:
            performed_at = datetime.now()

        if performed_at > datetime.now():
            raise BusinessRuleViolationError("Activity date cannot be in the future")

        start_date = program_found.start_date
        if performed_at.tzinfo is None and start_date.tzinfo is not None:
            performed_at = performed_at.replace(tzinfo=start_date.tzinfo)
        elif performed_at.tzinfo is not None and start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=performed_at.tzinfo)

        if performed_at < start_date:
            raise BusinessRuleViolationError(
                "Activity date is outside the program date range"
            )

        if program_found.end_date:
            end_date = program_found.end_date
            if performed_at.tzinfo is None and end_date.tzinfo is not None:
                performed_at = performed_at.replace(tzinfo=end_date.tzinfo)
            elif performed_at.tzinfo is not None and end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=performed_at.tzinfo)

            if performed_at > end_date:
                raise BusinessRuleViolationError(
                    "Activity date is outside the program date range"
                )

        return performed_at
