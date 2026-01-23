"""Create parlay_legs table for settlement tracking.

Revision ID: 038_create_parlay_legs_table
Revises: 037_add_live_scores_to_games
Create Date: 2026-01-XX
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "038_create_parlay_legs_table"
down_revision = "037_add_live_scores_to_games"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "parlay_legs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("parlay_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("saved_parlay_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("game_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("market_type", sa.String(), nullable=False),
        sa.Column("selection", sa.String(), nullable=False),
        sa.Column("line", sa.Numeric(), nullable=True),
        sa.Column("price", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="PENDING"),
        sa.Column("result_reason", sa.String(), nullable=True),
        sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["parlay_id"], ["parlays.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["saved_parlay_id"], ["saved_parlays.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"], ondelete="CASCADE"),
    )
    
    # Create indexes
    op.create_index("idx_parlay_legs_parlay_status", "parlay_legs", ["parlay_id", "status"])
    op.create_index("idx_parlay_legs_saved_parlay_status", "parlay_legs", ["saved_parlay_id", "status"])
    op.create_index("idx_parlay_legs_game_status", "parlay_legs", ["game_id", "status"])
    op.create_index("idx_parlay_legs_status_settled", "parlay_legs", ["status", "settled_at"])


def downgrade() -> None:
    op.drop_index("idx_parlay_legs_status_settled", table_name="parlay_legs")
    op.drop_index("idx_parlay_legs_game_status", table_name="parlay_legs")
    op.drop_index("idx_parlay_legs_saved_parlay_status", table_name="parlay_legs")
    op.drop_index("idx_parlay_legs_parlay_status", table_name="parlay_legs")
    op.drop_table("parlay_legs")
