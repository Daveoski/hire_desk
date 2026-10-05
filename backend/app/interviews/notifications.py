"""Interview update emails.

Every interview event (scheduled, cancelled, completed) emails the interviewer
plus the people who follow the pipeline: the job's hiring manager and every
company admin. send_email logs failures, so a bad address never fails a request.
"""
import uuid

from fastapi import BackgroundTasks
from sqlmodel import Session, select

from app.candidates.models import Application
from app.core.email import send_email
from app.interviews.models import Interview
from app.jobs.models import Job
from app.users.models import Role, User


def update_recipients(db: Session, job: Job) -> list[User]:
    """The job's hiring manager plus every company admin, without duplicates."""
    recipients: dict[uuid.UUID, User] = {}
    if job.hiring_manager_id:
        hiring_manager = db.get(User, job.hiring_manager_id)
        if hiring_manager is not None:
            recipients[hiring_manager.id] = hiring_manager
    admins = db.exec(select(User).where(User.company_id == job.company_id, User.role == Role.company_admin)).all()
    for admin in admins:
        recipients[admin.id] = admin
    return list(recipients.values())


def _minutes(interview: Interview) -> int:
    return int((interview.ends_at - interview.starts_at).total_seconds() // 60)


def _slot(interview: Interview) -> str:
    return f"{interview.starts_at.isoformat()} ({_minutes(interview)} minutes)"


def notify_scheduled(
    db: Session, background_tasks: BackgroundTasks, interview: Interview, application: Application, job: Job, interviewer: User
):
    """The interviewer learns they were scheduled; the manager and admin(s) get an update."""
    background_tasks.add_task(
        send_email,
        to=interviewer.email,
        subject=f"Interview assigned: {application.full_name} for {job.title}",
        text=(
            f"Hi {interviewer.full_name},\n\n"
            f"You have been scheduled to interview {application.full_name} for {job.title}.\n"
            f"Start: {_slot(interview)}\n\n"
            f"Please fill in your scorecard after the interview."
        ),
    )
    for recipient in update_recipients(db, job):
        background_tasks.add_task(
            send_email,
            to=recipient.email,
            subject=f"Interview scheduled: {application.full_name} for {job.title}",
            text=(
                f"Hi {recipient.full_name},\n\n"
                f"{interviewer.full_name} has been scheduled to interview {application.full_name} "
                f"for {job.title}.\nStart: {_slot(interview)}"
            ),
        )


def notify_cancelled(
    db: Session, background_tasks: BackgroundTasks, interview: Interview, application: Application, job: Job, interviewer: User
):
    for recipient in update_recipients(db, job):
        background_tasks.add_task(
            send_email,
            to=recipient.email,
            subject=f"Interview cancelled: {application.full_name} for {job.title}",
            text=(
                f"Hi {recipient.full_name},\n\n"
                f"The interview of {interviewer.full_name} with {application.full_name} for {job.title} "
                f"({interview.starts_at.isoformat()}) has been cancelled. The time slot is free again."
            ),
        )


def notify_completed(
    db: Session, background_tasks: BackgroundTasks, interview: Interview, application: Application, job: Job, interviewer: User
):
    for recipient in update_recipients(db, job):
        background_tasks.add_task(
            send_email,
            to=recipient.email,
            subject=f"Interview completed: {application.full_name} for {job.title}",
            text=(
                f"Hi {recipient.full_name},\n\n"
                f"{interviewer.full_name} submitted the scorecard for the interview with "
                f"{application.full_name} for {job.title} (held at {interview.starts_at.isoformat()})."
            ),
        )
