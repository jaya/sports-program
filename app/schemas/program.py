from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ProgramBase(BaseModel):
    name: str
    slack_channel: str
    start_date: datetime
    end_date: datetime | None = None


class ProgramCreate(ProgramBase):
    pass


class ProgramResponse(ProgramBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
