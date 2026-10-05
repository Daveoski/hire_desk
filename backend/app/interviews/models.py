import uuid
from datetime import datetime
from enum import StrEnum

from sqlmodel import Field, SQLModel

from app.db.common import TIMESTAMPTZ, enum_column


class InterviewStatus(StrEnum):
    scheduled = "scheduled"
    completed = "completed"  # set when the interviewer submits the scorecard
    cancelled = "cancelled"


class Interview(SQLModel, table=True):
    """One interviewer, one time slot, one candidate application.

    Clash prevention lives in the database: the migration adds an exclusion
    constraint (no_overlapping_interviews) so one interviewer can never have two
    overlapping interviews unless one of them is cancelled.
    The start and end are stored; the duration is calculated from them.
    """

    __tablename__ = "interviews"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    application_id: uuid.UUID = Field(foreign_key="applications.id", index=True)
    interviewer_id: uuid.UUID = Field(foreign_key="users.id")
    starts_at: datetime = Field(sa_type=TIMESTAMPTZ)
    ends_at: datetime = Field(sa_type=TIMESTAMPTZ)
    status: InterviewStatus = Field(default=InterviewStatus.scheduled, sa_type=enum_column(InterviewStatus))
    # Google Calendar sync: the event pushed on the owner's calendar, if any.
    google_event_id: str | None = Field(default=None)
    google_calendar_id: str | None = Field(default=None)
    google_owner_id: uuid.UUID | None = Field(default=None, foreign_key="users.id")
