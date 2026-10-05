import uuid
from datetime import datetime, timezone

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, computed_field, field_validator

from app.interviews.models import InterviewStatus


class InterviewCreate(BaseModel):
    application_id: uuid.UUID
    interviewer_id: uuid.UUID
    starts_at: AwareDatetime  # must include a timezone, for example 2026-11-02T10:00:00+01:00
    duration_minutes: int = Field(ge=15, le=240)

    @field_validator("starts_at")
    @classmethod
    def must_be_in_the_future(cls, starts_at: datetime) -> datetime:
        if starts_at <= datetime.now(timezone.utc):
            raise ValueError("starts_at must be in the future")
        return starts_at


class InterviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    application_id: uuid.UUID
    interviewer_id: uuid.UUID
    starts_at: datetime
    ends_at: datetime
    status: InterviewStatus

    @computed_field
    @property
    def duration_minutes(self) -> int:
        return int((self.ends_at - self.starts_at).total_seconds() // 60)
