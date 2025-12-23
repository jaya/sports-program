from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator

from app.exceptions.business import BusinessRuleViolationError
from app.schemas.program import ProgramSimple
from app.schemas.user import UserBase
from app.utils.date_validator import is_within_allowed_window


class DateValidation(BaseModel):
    @field_validator("performed_at", check_fields=False)
    @classmethod
    def validate_performed_at(cls, value: datetime | None):
        if value is None:
            return value

        if not is_within_allowed_window(value):
            raise BusinessRuleViolationError(
                "The date of the activity must be in the current or previous month."
            )
        return value


class ActivityBase(BaseModel):
    description: str
    evidence_url: str | None = None
    performed_at: datetime | None = None


class ActivityCreate(ActivityBase, DateValidation):
    pass


class ActivityUpdate(ActivityBase, DateValidation):
    description: str | None = None
    evidence_url: str | None = None
    performed_at: datetime | None = None

    model_config = ConfigDict(extra='forbid')


class ActivitySummaryResponse(BaseModel):
    id: int
    count_month: int

    model_config = ConfigDict(from_attributes=True)


class ActivityResponse(ActivityBase):
    id: int
    created_at: datetime
    user: Optional[UserBase] = None
    program: Optional[ProgramSimple] = None

    model_config = ConfigDict(from_attributes=True)
