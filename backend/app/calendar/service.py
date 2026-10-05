"""Creating and deleting the Google Calendar events of interviews.

The event lives on the calendar of the manager who scheduled the interview; the
interviewer is an attendee, so Google invites them too. Sync is best effort: a
Google problem is logged, never raised - an interview must not fail because of it.
"""
import logging
from datetime import timedelta

from sqlmodel import Session

from app.calendar import google
from app.calendar.models import GoogleToken
from app.core.config import get_settings
from app.db.common import utcnow
from app.interviews.models import Interview
from app.users.models import User

logger = logging.getLogger(__name__)


def _access_token(db: Session, token: GoogleToken) -> str:
    """A valid access token, refreshed through Google when it has almost expired."""
    if token.expires_at > utcnow() + timedelta(seconds=60):
        return token.access_token
    if not token.refresh_token:
        raise RuntimeError("The Google connection has no refresh token; reconnect Google Calendar")
    tokens = google.refresh_access_token(token.refresh_token)
    token.access_token = tokens["access_token"]
    token.expires_at = utcnow() + timedelta(seconds=tokens.get("expires_in", 3600))
    db.add(token)
    db.commit()
    return token.access_token


def sync_interview_event(
    db: Session, owner: User, interview: Interview, application, job, interviewer
) -> bool:
    """Push a just-scheduled interview to the owner's Google Calendar. True when synced."""
    if not google.is_configured():
        return False
    token = db.get(GoogleToken, owner.id)
    if token is None:
        return False
    try:
        access_token = _access_token(db, token)
        event_id = google.create_event(
            access_token,
            summary=f"Interview: {application.full_name} - {job.title}",
            description=(
                f"{interviewer.full_name} interviews {application.full_name} for {job.title}.\n"
                f"Candidate profile: {get_settings().frontend_url}/candidates/{application.id}"
            ),
            starts_at=interview.starts_at,
            ends_at=interview.ends_at,
            attendees=[interviewer.email],
        )
        interview.google_event_id = event_id
        interview.google_calendar_id = "primary"
        interview.google_owner_id = owner.id
        db.add(interview)
        db.commit()
        return True
    except Exception:
        logger.exception("Could not sync interview %s to Google Calendar", interview.id)
        return False


def remove_interview_event(db: Session, interview: Interview) -> None:
    """Delete the interview's calendar event. The ids are cleared even when Google fails."""
    if not interview.google_event_id or not interview.google_owner_id:
        return
    token = db.get(GoogleToken, interview.google_owner_id)
    try:
        if token is not None:
            google.delete_event(_access_token(db, token), interview.google_event_id)
    except Exception:
        logger.exception("Could not delete the Google Calendar event of interview %s", interview.id)
    finally:
        interview.google_event_id = None
        interview.google_calendar_id = None
        interview.google_owner_id = None
        db.add(interview)
        db.commit()
