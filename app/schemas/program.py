from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ProgramBase(BaseModel):
    name: str
    slack_channel: str
    start_date: datetime
    end_date: datetime | None = None


class ProgramSimple(BaseModel):
    name: str
    slack_channel: str


class ProgramCreate(ProgramBase):
    pass


class ProgramUpdate(ProgramBase):
    name: str | None = None
    slack_channel: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None

    model_config = ConfigDict(extra='forbid')


class ProgramResponse(ProgramBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
