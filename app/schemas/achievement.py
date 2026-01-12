from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.program import ProgramSimple
from app.schemas.user_schema import UserBase


class AchievementBase(BaseModel):
    cycle_reference: str
    is_notified: bool


class AchievementCreate(BaseModel):
    cycle_reference: str


class AchievementBatchCreate(BaseModel):
    user_ids: list[int]
    program_id: int
    program_name: str
    cycle_reference: str


class AchievementBatchResponse(BaseModel):
    total_created: int
    program_name: str
    cycle_reference: str
    users: list[str]


class AchievementResponse(AchievementBase):
    id: int
    user: UserBase
    program: ProgramSimple
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
