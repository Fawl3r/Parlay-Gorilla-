"""Create parlay_feed_events table for marquee and win wall.

Revision ID: 040_create_parlay_feed_events
Revises: 039_add_settlement_to_parlays
Create Date: 2026-01-XX
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "040_create_parlay_feed_events"
down_revision = "039_add_settlement_to_parlays"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "parlay_feed_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("sport", sa.String(), nullable=True),
        sa.Column("parlay_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("saved_parlay_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_alias", sa.String(), nullable=True),
        sa.Column("summary", sa.String(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.ForeignKeyConstraint(["parlay_id"], ["parlays.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["saved_parlay_id"], ["saved_parlays.id"], ondelete="CASCADE"),
    )
    
    # Create indexes (DESC ordering handled in queries via ORDER BY)
    op.create_index("idx_feed_events_created_at", "parlay_feed_events", ["created_at"])
    op.create_index("idx_feed_events_type_created", "parlay_feed_events", ["event_type", "created_at"])
    op.create_index("idx_feed_events_sport_created", "parlay_feed_events", ["sport", "created_at"])


def downgrade() -> None:
    op.drop_index("idx_feed_events_sport_created", table_name="parlay_feed_events")
    op.drop_index("idx_feed_events_type_created", table_name="parlay_feed_events")
    op.drop_index("idx_feed_events_created_at", table_name="parlay_feed_events")
    op.drop_table("parlay_feed_events")
