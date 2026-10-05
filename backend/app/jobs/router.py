import uuid

from fastapi import APIRouter, HTTPException
from sqlmodel import Session, col

from app.auth.dependencies import AdminUser, ManagerUser
from app.auth.permissions import get_visible_job, visible_jobs
from app.db.session import DbSession
from app.jobs.models import Job
from app.jobs.schemas import JobCreate, JobRead, JobUpdate
from app.users.models import Role, User

router = APIRouter(prefix="/jobs", tags=["Jobs"])


def check_hiring_manager(db: Session, admin: User, hiring_manager_id: uuid.UUID | None) -> None:
    if hiring_manager_id is None:
        return
    manager = db.get(User, hiring_manager_id)
    if manager is None or manager.company_id != admin.company_id or manager.role != Role.hiring_manager:
        raise HTTPException(422, "hiring_manager_id must be a hiring manager of your company")


@router.post("", response_model=JobRead, status_code=201)
def create_job(body: JobCreate, admin: AdminUser, db: DbSession):
    """New jobs start as drafts. Set status to "open" to publish the public application page."""
    check_hiring_manager(db, admin, body.hiring_manager_id)
    job = Job(company_id=admin.company_id, **body.model_dump())
    db.add(job)
    db.commit()
    return job


@router.get("", response_model=list[JobRead])
def list_jobs(manager: ManagerUser, db: DbSession):
    return db.exec(visible_jobs(manager).order_by(col(Job.created_at).desc())).all()


@router.get("/{job_id}", response_model=JobRead)
def read_job(job_id: uuid.UUID, manager: ManagerUser, db: DbSession):
    return get_visible_job(db, manager, job_id)


@router.patch("/{job_id}", response_model=JobRead)
def update_job(job_id: uuid.UUID, body: JobUpdate, admin: AdminUser, db: DbSession):
    job = get_visible_job(db, admin, job_id)
    changes = body.model_dump(exclude_unset=True)
    if "hiring_manager_id" in changes:
        check_hiring_manager(db, admin, changes["hiring_manager_id"])
    for field, value in changes.items():
        setattr(job, field, value)
    db.add(job)
    db.commit()
    return job
