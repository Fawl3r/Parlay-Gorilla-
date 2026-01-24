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
    from sqlalchemy import inspect
    from sqlalchemy.exc import ProgrammingError
    
    conn = op.get_bind()
    
    # Check if table exists using direct SQL query (more reliable than inspector)
    def table_exists(table_name: str) -> bool:
        result = conn.execute(sa.text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = :name)"
        ), {"name": table_name})
        return result.scalar()
    
    # Create table if it doesn't exist
    if not table_exists("system_heartbeats"):
        try:
            op.create_table(
                "system_heartbeats",
                sa.Column("name", sa.String(), primary_key=True, nullable=False),
                sa.Column("last_beat_at", sa.DateTime(timezone=True), nullable=False),
                sa.Column("meta", postgresql.JSONB(), nullable=True),
            )
        except ProgrammingError as e:
            # Table might exist even if check didn't catch it
            error_str = str(e).lower()
            if "already exists" not in error_str and "duplicate" not in error_str:
                raise


def downgrade() -> None:
    op.drop_table("system_heartbeats")
