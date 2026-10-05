import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.candidates.models import Application
from app.jobs.models import Job, Stage

FINAL_STAGES = (Stage.hired, Stage.rejected)


class ApplicationRead(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    job_title: str
    job_hiring_manager_id: uuid.UUID | None
    full_name: str
    email: str
    phone: str
    cv_url: str
    cover_letter: str | None
    stage: Stage
    created_at: datetime

    @classmethod
    def from_rows(cls, application: Application, job: Job) -> "ApplicationRead":
        return cls(**application.model_dump(), job_title=job.title, job_hiring_manager_id=job.hiring_manager_id)


class ApplicationReceipt(BaseModel):
    """What a candidate gets back after applying."""

    id: uuid.UUID
    created_at: datetime


class StageMove(BaseModel):
    """Move a candidate forward to screen, interview or offer."""

    stage: Stage

    @field_validator("stage")
    @classmethod
    def not_a_final_stage(cls, stage: Stage) -> Stage:
        if stage in FINAL_STAGES:
            raise ValueError("Use the decision endpoint to hire or reject a candidate")
        return stage


class DecisionRequest(BaseModel):
    """The hiring decision. The value must be "hired" or "rejected"."""

    decision: Stage

    @field_validator("decision")
    @classmethod
    def must_be_a_final_stage(cls, decision: Stage) -> Stage:
        if decision not in FINAL_STAGES:
            raise ValueError('decision must be "hired" or "rejected"')
        return decision


class StageHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    from_stage: Stage | None
    to_stage: Stage
    changed_by_id: uuid.UUID | None
    changed_at: datetime
