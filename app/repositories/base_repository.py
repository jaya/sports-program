import structlog
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

logger = structlog.get_logger()

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
            logger.debug("Entity created successfully", entity=self.model.__name__, id=getattr(obj_in, "id", None))
        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to create entity", entity=self.model.__name__, error=str(e))
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
            logger.debug("Entity updated successfully", entity=self.model.__name__, id=getattr(obj_in, "id", None))
        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to update entity", entity=self.model.__name__, error=str(e))
            raise
        return obj_in

    async def create_many(self, objs: list[ModelType]) -> list[ModelType]:
        if not objs:
            return []
        self.session.add_all(objs)
        try:
            await self.session.commit()
            logger.debug("Multiple entities created", entity=self.model.__name__, count=len(objs), batch=True)
            return objs
        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to create entity", entity=self.model.__name__, error=str(e), batch=True)
            raise
