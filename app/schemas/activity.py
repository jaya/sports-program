from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ActivityBase(BaseModel):
    description: str
    evidence_url: str | None = None
    performed_at: datetime | None = None


class ActivityCreate(ActivityBase):
    pass


class ActivityResponse(ActivityBase):
    id: int
    user_id: int
    program_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
