import uuid

from fastapi import APIRouter, Query
from sqlmodel import col, select

from app.auth.dependencies import CurrentUser, ManagerUser
from app.auth.permissions import get_visible_application, visible_applications
from app.candidates.models import Application, StageHistory
from app.candidates.schemas import (
    ApplicationRead,
    DecisionRequest,
    StageHistoryRead,
    StageMove,
)
from app.candidates.service import change_stage
from app.db.session import DbSession
from app.jobs.models import Stage

router = APIRouter(prefix="/applications", tags=["Candidates"])


@router.get("", response_model=list[ApplicationRead])
def list_applications(
    user: CurrentUser,
    db: DbSession,
    job_id: uuid.UUID | None = None,
    stage: Stage | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Admins and hiring managers see their jobs' candidates. Interviewers see only assigned ones."""
    query = visible_applications(user)
    if job_id is not None:
        query = query.where(Application.job_id == job_id)
    if stage is not None:
        query = query.where(Application.stage == stage)
    rows = db.exec(query.order_by(col(Application.created_at).desc()).offset(offset).limit(limit)).all()
    return [ApplicationRead.from_rows(application, job) for application, job in rows]


@router.get("/{application_id}", response_model=ApplicationRead)
def read_application(application_id: uuid.UUID, user: CurrentUser, db: DbSession):
    application, job = get_visible_application(db, user, application_id)
    return ApplicationRead.from_rows(application, job)


@router.patch("/{application_id}/stage", response_model=ApplicationRead)
def move_application(application_id: uuid.UUID, body: StageMove, manager: ManagerUser, db: DbSession):
    """Move a candidate forward: applied -> screen -> interview -> offer."""
    _, job = get_visible_application(db, manager, application_id)
    application = change_stage(db, application_id, body.stage, manager)
    return ApplicationRead.from_rows(application, job)


@router.post("/{application_id}/decision", response_model=ApplicationRead)
def decide_application(application_id: uuid.UUID, body: DecisionRequest, manager: ManagerUser, db: DbSession):
    """The final decision. A candidate can only be hired from the offer stage."""
    _, job = get_visible_application(db, manager, application_id)
    application = change_stage(db, application_id, body.decision, manager)
    return ApplicationRead.from_rows(application, job)


@router.get("/{application_id}/history", response_model=list[StageHistoryRead])
def read_stage_history(application_id: uuid.UUID, manager: ManagerUser, db: DbSession):
    get_visible_application(db, manager, application_id)  # 404 if the manager cannot see it
    return db.exec(
        select(StageHistory)
        .where(StageHistory.application_id == application_id)
        .order_by(col(StageHistory.changed_at))
    ).all()
