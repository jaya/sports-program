from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.slack_installation import SlackState
from app.repositories.base_repository import BaseRepository


class SlackStateRepository(BaseRepository[SlackState]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, SlackState)

    async def find_by_state(self, state: str) -> SlackState | None:
        stmt = select(SlackState).where(SlackState.state == state)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_by_state(self, state: str) -> None:
        db_state = await self.find_by_state(state)
        if db_state:
            await self.session.delete(db_state)
            await self.session.commit()
