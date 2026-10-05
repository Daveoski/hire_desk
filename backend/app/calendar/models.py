import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel

from app.db.common import TIMESTAMPTZ


class GoogleToken(SQLModel, table=True):
    """The Google OAuth tokens of one connected user (their calendar to sync to)."""

    __tablename__ = "google_tokens"

    user_id: uuid.UUID = Field(foreign_key="users.id", primary_key=True)
    access_token: str
    # Google only returns a refresh token on the first consent, so keep the old one.
    refresh_token: str | None = None
    expires_at: datetime = Field(sa_type=TIMESTAMPTZ)
