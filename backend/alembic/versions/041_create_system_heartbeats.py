"""Create system_heartbeats table for proof of checking.

Revision ID: 041_create_system_heartbeats
Revises: 040_create_parlay_feed_events
Create Date: 2026-01-XX
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "041_create_system_heartbeats"
down_revision = "040_create_parlay_feed_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "system_heartbeats",
        sa.Column("name", sa.String(), primary_key=True, nullable=False),
        sa.Column("last_beat_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("meta", postgresql.JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("system_heartbeats")
