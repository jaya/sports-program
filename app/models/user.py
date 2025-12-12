from datetime import datetime
from pydantic import BaseModel, ConfigDict

class UserBase(BaseModel):
    slack_id: str
    display_name: str

class UserCreate(UserBase):
    pass

class UserRead(UserBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
