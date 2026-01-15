from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, session: AsyncSession, model: type[ModelType]):
        self.session = session
        self.model = model

    async def create(self, obj_in: ModelType) -> ModelType:
        self.session.add(obj_in)
        try:
            await self.session.commit()
            await self.session.refresh(obj_in)
        except Exception:
            await self.session.rollback()
            raise
        return obj_in

    async def get_by_id(self, item_id: int) -> ModelType | None:
        query = select(self.model).where(self.model.id == item_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_all(self) -> list[ModelType]:
        query = select(self.model)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, obj_in: ModelType) -> ModelType | None:
        self.session.add(obj_in)
        try:
            await self.session.commit()
            await self.session.refresh(obj_in)
        except Exception:
            await self.session.rollback()
            raise
        return obj_in

    async def create_many(self, objs: list[ModelType]) -> list[ModelType]:
        if not objs:
            return []
        self.session.add_all(objs)
        try:
            await self.session.commit()
            return objs
        except Exception:
            await self.session.rollback()
            raise
