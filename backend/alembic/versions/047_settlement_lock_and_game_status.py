"""Add settlement_locked_at for stat-correction window; no schema change for game status (status is string).

Revision ID: 047_settlement_lock_and_game_status
Revises: 046_add_user_metadata_columns
Create Date: 2026-02-05

Settlement MUST NOT assume date-based completion. This migration adds:
- parlay_legs.settlement_locked_at: set on first settlement; enables one controlled re-evaluation
  window (e.g. 24-72h) for stat corrections with explicit logging.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "047_settlement_lock_and_game_status"
down_revision = "046_add_user_metadata_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Settlement lock: when we first settle a leg we set this; allows one re-eval within 72h for stat corrections
    op.add_column(
        "parlay_legs",
        sa.Column("settlement_locked_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("parlay_legs", "settlement_locked_at")
