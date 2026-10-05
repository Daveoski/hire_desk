"""Plain-HTTP Google OAuth and Calendar calls (no Google SDK needed)."""
import logging
from datetime import datetime

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
SCOPES = ["openid", "email", "https://www.googleapis.com/auth/calendar.events"]


def is_configured() -> bool:
    settings = get_settings()
    return bool(settings.google_client_id and settings.google_client_secret and settings.google_redirect_uri)


def build_auth_url(state: str) -> str:
    settings = get_settings()
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        # offline access + consent so we always receive a refresh token.
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return str(httpx.Request("GET", AUTH_URL, params=params).url)


def _token_request(data: dict) -> dict:
    settings = get_settings()
    response = httpx.post(TOKEN_URL, data={**data, "client_id": settings.google_client_id, "client_secret": settings.google_client_secret}, timeout=10)
    response.raise_for_status()
    return response.json()


def exchange_code(code: str) -> dict:
    return _token_request({"grant_type": "authorization_code", "code": code, "redirect_uri": get_settings().google_redirect_uri})


def refresh_access_token(refresh_token: str) -> dict:
    return _token_request({"grant_type": "refresh_token", "refresh_token": refresh_token})


def create_event(
    access_token: str, *, summary: str, description: str, starts_at: datetime, ends_at: datetime, attendees: list[str]
) -> str:
    """Create an event on the primary calendar; the attendees get Google invitations. Returns the event id."""
    body = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": starts_at.isoformat()},
        "end": {"dateTime": ends_at.isoformat()},
        "attendees": [{"email": email} for email in attendees],
    }
    response = httpx.post(
        EVENTS_URL, json=body, headers={"Authorization": f"Bearer {access_token}"}, timeout=10
    )
    response.raise_for_status()
    return response.json()["id"]


def delete_event(access_token: str, event_id: str) -> None:
    response = httpx.delete(
        f"{EVENTS_URL}/{event_id}", headers={"Authorization": f"Bearer {access_token}"}, timeout=10
    )
    # 404/410: the event is already gone, which is all we wanted.
    if response.status_code not in (200, 204, 404, 410):
        response.raise_for_status()
