from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager

from app.models.activity import Activity
from app.models.program import Program
from app.models.user import User
from app.repositories.base_repository import BaseRepository


class ActivityRepository(BaseRepository[Activity]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Activity)

    async def find_by_user_id_and_date(
        self, user_id: int, year: int, month: int
    ) -> list[Activity]:
        stmt = (
            select(Activity)
            .join(Activity.user)
            .join(Activity.program)
            .where(
                Activity.user_id == user_id,
                Activity.filter_date_tz(year, month),
            )
            .options(contains_eager(Activity.user), contains_eager(Activity.program))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_id_and_slack_id(
        self, id: int, slack_id: str
    ) -> Activity | None:
        stmt = (
            select(Activity)
            .join(Activity.user)
            .join(Activity.program)
            .where(Activity.id == id, User.slack_id == slack_id)
            .options(contains_eager(Activity.user), contains_eager(Activity.program))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_user_id_and_slack_channel_and_date(
        self, user_id: int, slack_channel: str, year: int, month: int
    ) -> list[Activity]:
        stmt = (
            select(Activity)
            .join(Activity.user)
            .join(Activity.program)
            .where(
                Activity.user_id == user_id,
                Program.slack_channel == slack_channel,
                Activity.filter_date_tz(year, month),
            )
            .options(contains_eager(Activity.user), contains_eager(Activity.program))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_monthly(self, user_id: int, year: int, month: int) -> int:
        stmt = select(func.count(Activity.id)).where(
            Activity.user_id == user_id, Activity.filter_date_tz(year, month)
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def check_activity_same_day(
        self,
        program_id: int,
        user_id: int,
        activity_date: date,
        exclude_id: int | None = None,
    ) -> Activity | None:
        stmt = select(Activity).where(
            Activity.user_id == user_id,
            Activity.program_id == program_id,
            func.date(Activity.performed_at) == activity_date,
        )
        if exclude_id is not None:
            stmt = stmt.where(Activity.id != exclude_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def find_users_with_completed_program(
        self, program_id: int, year: int, month: int, goal: int
    ) -> list[int]:
        stmt = (
            select(Activity.user_id)
            .where(
                Activity.program_id == program_id, Activity.filter_date_tz(year, month)
            )
            .group_by(Activity.user_id)
            .having(func.count(Activity.id) >= goal)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
