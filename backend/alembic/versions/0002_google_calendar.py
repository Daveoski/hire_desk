"""google calendar sync

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "google_tokens",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("access_token", sa.String(), nullable=False),
        sa.Column("refresh_token", sa.String(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("user_id"),
    )

    # Which Google Calendar event an interview was pushed to, and by whom.
    op.add_column("interviews", sa.Column("google_event_id", sa.String(), nullable=True))
    op.add_column("interviews", sa.Column("google_calendar_id", sa.String(), nullable=True))
    op.add_column("interviews", sa.Column("google_owner_id", sa.Uuid(), nullable=True))
    op.create_foreign_key("fk_interviews_google_owner_id", "interviews", "users", ["google_owner_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_interviews_google_owner_id", "interviews", type_="foreignkey")
    op.drop_column("interviews", "google_owner_id")
    op.drop_column("interviews", "google_calendar_id")
    op.drop_column("interviews", "google_event_id")
    op.drop_table("google_tokens")
