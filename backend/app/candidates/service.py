import uuid

from fastapi import HTTPException
from sqlmodel import Session, select

from app.candidates.models import Application, StageHistory
from app.jobs.models import Job, Stage
from app.users.models import Role, User


def ensure_screener(user: User, job: Job) -> None:
    """Screening (moving a candidate into or out of the screen stage) is the hiring
    manager's job; a company admin may screen only a job that has no hiring manager."""
    if user.role == Role.hiring_manager and job.hiring_manager_id == user.id:
        return
    if user.role == Role.company_admin and job.hiring_manager_id is None:
        return
    raise HTTPException(403, "Only this job's hiring manager can screen candidates")

# The pipeline rules: a candidate moves one step forward, or is rejected from any open stage.
ALLOWED_TRANSITIONS: dict[Stage, set[Stage]] = {
    Stage.applied: {Stage.screen, Stage.rejected},
    Stage.screen: {Stage.interview, Stage.rejected},
    Stage.interview: {Stage.offer, Stage.rejected},
    Stage.offer: {Stage.hired, Stage.rejected},
    Stage.hired: set(),
    Stage.rejected: set(),
}


def change_stage(db: Session, application_id: uuid.UUID, new_stage: Stage, user: User) -> Application:
    """Move an application to a new stage and record it in the stage history.

    The application row is locked (SELECT ... FOR UPDATE) until commit. If two requests
    change the same candidate at the same time, the second one waits, then sees the
    stage the first one set and is checked against it. So the history never contains
    two rows that claim the same "from" stage.
    """
    # populate_existing makes sure we read the stage as it is now, not an older copy
    # that this session loaded before the lock was taken.
    application = db.exec(
        select(Application)
        .where(Application.id == application_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).one()

    if new_stage not in ALLOWED_TRANSITIONS[application.stage]:
        raise HTTPException(
            409,
            f"A candidate in '{application.stage.value}' cannot be moved to '{new_stage.value}'",
        )

    db.add(
        StageHistory(
            application_id=application.id,
            from_stage=application.stage,
            to_stage=new_stage,
            changed_by_id=user.id,
        )
    )
    application.stage = new_stage
    db.add(application)
    db.commit()
    return application
