from typing import Generic, TypeVar, Type, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, session: AsyncSession, model: Type[ModelType]):
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

    async def get_by_id(self, id: int) -> Optional[ModelType]:
        query = select(self.model).where(self.model.id == id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_all(self) -> List[ModelType]:
        query = select(self.model)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update(self, obj_in: ModelType) -> Optional[ModelType]:
        self.session.add(obj_in)
        try:
            await self.session.commit()
            await self.session.refresh(obj_in)
        except Exception:
            await self.session.rollback()
            raise
        return obj_in
