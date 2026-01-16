from typing import Annotated

from fastapi import Depends
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.database import get_db
from app.models.achievement import Achievement
from app.repositories.base_repository import BaseRepository


class AchievementRepository(BaseRepository[Achievement]):
    def __init__(
        self,
        session: Annotated[AsyncSession, Depends(get_db)],
    ):
        super().__init__(session, Achievement)

    async def find_existing_user_ids(
        self, program_id: int, cycle_reference: str, user_ids: list[int]
    ) -> set[int]:
        stmt = select(Achievement.user_id).where(
            Achievement.program_id == program_id,
            Achievement.cycle_reference == cycle_reference,
            Achievement.user_id.in_(user_ids),
        )
        result = await self.session.execute(stmt)
        return set(result.scalars().all())

    async def find_pending_notification(
        self, program_id: int, cycle_reference: str
    ) -> list[Achievement]:
        stmt = (
            select(Achievement)
            .options(
                joinedload(Achievement.user),
                joinedload(Achievement.program)
            )
            .where(
                Achievement.program_id == program_id,
                Achievement.cycle_reference == cycle_reference,
                Achievement.is_notified.is_(False),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().unique().all()

    async def mark_as_notified(self, achievement_ids: list[int]) -> int:
        if not achievement_ids:
            return 0

        stmt = (
            update(Achievement)
            .where(Achievement.id.in_(achievement_ids))
            .values(is_notified=True)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount
