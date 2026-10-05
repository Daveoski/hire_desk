"""The Google Calendar connect flow (per user) and disconnect."""
import logging

from datetime import timedelta

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from sqlmodel import Session

from app.calendar import google
from app.calendar.models import GoogleToken
from app.auth.dependencies import CurrentUser
from app.core.config import get_settings
from app.core.security import create_access_token, decode_access_token
from app.db.common import utcnow
from app.db.session import DbSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calendar", tags=["Calendar"])


@router.get("/google/authorize")
def authorize(user: CurrentUser):
    """The URL the browser must open to connect this user's Google account."""
    if not google.is_configured():
        raise HTTPException(
            503, "Google Calendar is not configured. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET."
        )
    # A short-lived signed token identifies the user across the Google redirect.
    return {"url": google.build_auth_url(create_access_token(user.id))}


@router.get("/google/callback")
def callback(code: str, state: str, db: DbSession):
    """Where Google sends the browser back after consent. Tokens are stored for the user in `state`."""
    user_id = decode_access_token(state)
    if user_id is None:
        raise HTTPException(401, "The connection link expired. Start the connection again.")
    try:
        tokens = google.exchange_code(code)
    except Exception:
        logger.exception("The Google token exchange failed")
        raise HTTPException(502, "Google refused the connection. Please try again.") from None

    token = db.get(GoogleToken, user_id)  # a second consent overwrites the first
    if token is None:
        token = GoogleToken(user_id=user_id)
    token.access_token = tokens["access_token"]
    token.refresh_token = tokens.get("refresh_token", token.refresh_token)
    token.expires_at = utcnow() + timedelta(seconds=tokens.get("expires_in", 3600))
    db.add(token)
    db.commit()
    return RedirectResponse(f"{get_settings().frontend_url}/interviews?google=connected")


@router.get("/google/status")
def status(user: CurrentUser, db: DbSession):
    return {"connected": db.get(GoogleToken, user.id) is not None}


@router.delete("/google")
def disconnect(user: CurrentUser, db: DbSession):
    token = db.get(GoogleToken, user.id)
    if token is not None:
        db.delete(token)
        db.commit()
    return {"connected": False}
