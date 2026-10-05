import uuid
from datetime import timedelta

from fastapi import APIRouter, BackgroundTasks, HTTPException
from psycopg.errors import ExclusionViolation
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col

from app.auth.dependencies import CurrentUser, ManagerUser
from app.auth.permissions import get_visible_application, get_visible_interview, visible_interviews
from app.calendar.service import remove_interview_event, sync_interview_event
from app.candidates.models import Application
from app.db.session import DbSession
from app.interviews.models import Interview, InterviewStatus
from app.interviews.notifications import notify_cancelled, notify_scheduled
from app.interviews.schemas import InterviewCreate, InterviewRead
from app.jobs.models import Job, Stage
from app.scorecards.models import Scorecard
from app.users.models import Role, User

router = APIRouter(prefix="/interviews", tags=["Interviews"])


def interview_context(db: Session, interview: Interview) -> tuple[Application, Job, User]:
    """The rows an email needs: the candidate, the job and the interviewer."""
    application = db.get(Application, interview.application_id)
    job = db.get(Job, application.job_id)
    interviewer = db.get(User, interview.interviewer_id)
    return application, job, interviewer


@router.post("", response_model=InterviewRead, status_code=201)
def schedule_interview(
    body: InterviewCreate,
    manager: ManagerUser,
    db: DbSession,
    background_tasks: BackgroundTasks,
):
    application, job = get_visible_application(db, manager, body.application_id)
    if application.stage in (Stage.hired, Stage.rejected):
        raise HTTPException(409, "This candidate's hiring process is already finished")

    interviewer = db.get(User, body.interviewer_id)
    if interviewer is None or interviewer.company_id != manager.company_id or interviewer.role != Role.interviewer:
        raise HTTPException(422, "interviewer_id must be an interviewer of your company")

    interview = Interview(
        application_id=application.id,
        interviewer_id=interviewer.id,
        starts_at=body.starts_at,
        ends_at=body.starts_at + timedelta(minutes=body.duration_minutes),
    )
    try:
        db.add(interview)
        db.flush()  # the database rejects an overlapping interview right here
        db.add(Scorecard(interview_id=interview.id))  # the interviewer receives an empty scorecard
        db.commit()
    except IntegrityError as error:
        db.rollback()
        if isinstance(error.orig, ExclusionViolation):
            raise HTTPException(409, "This interviewer already has an interview at that time") from error
        raise

    # The calendar event is created on the scheduling manager's Google Calendar
    # (best effort: a Google problem is logged, the interview itself stands).
    sync_interview_event(db, manager, interview, application, job, interviewer)
    # Emails to the interviewer plus the hiring manager and company admin(s).
    notify_scheduled(db, background_tasks, interview, application, job, interviewer)
    return interview


@router.get("", response_model=list[InterviewRead])
def list_interviews(user: CurrentUser, db: DbSession, application_id: uuid.UUID | None = None):
    """Managers see their jobs' interviews. Interviewers see only their own."""
    query = visible_interviews(user)
    if application_id is not None:
        query = query.where(Interview.application_id == application_id)
    return db.exec(query.order_by(col(Interview.starts_at))).all()


@router.get("/{interview_id}", response_model=InterviewRead)
def read_interview(interview_id: uuid.UUID, user: CurrentUser, db: DbSession):
    return get_visible_interview(db, user, interview_id)


@router.post("/{interview_id}/cancel", response_model=InterviewRead)
def cancel_interview(interview_id: uuid.UUID, manager: ManagerUser, db: DbSession, background_tasks: BackgroundTasks):
    """Cancelling frees the interviewer's time slot and removes the calendar event."""
    interview = get_visible_interview(db, manager, interview_id)
    if interview.status != InterviewStatus.scheduled:
        raise HTTPException(409, f"A {interview.status.value} interview cannot be cancelled")
    interview.status = InterviewStatus.cancelled
    db.add(interview)
    db.commit()

    application, job, interviewer = interview_context(db, interview)
    remove_interview_event(db, interview)
    notify_cancelled(db, background_tasks, interview, application, job, interviewer)
    return interview
