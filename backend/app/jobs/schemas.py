import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.jobs.models import JobStatus, Stage


class JobCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=10000)
    hiring_manager_id: uuid.UUID | None = None


class JobUpdate(BaseModel):
    """Only the fields that are sent are changed. hiring_manager_id may be set to null."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1, max_length=10000)
    status: JobStatus | None = None
    hiring_manager_id: uuid.UUID | None = None

    @field_validator("title", "description", "status")
    @classmethod
    def cannot_be_null(cls, value):
        if value is None:
            raise ValueError("cannot be null")
        return value


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str
    status: JobStatus
    hiring_manager_id: uuid.UUID | None
    created_at: datetime
    # Every job uses the same default pipeline; the Job table has no stages column.
    stages: list[Stage] = list(Stage)
