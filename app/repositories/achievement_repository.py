from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
