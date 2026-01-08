"""Add inscription_credits_consumed flag to saved_parlays.

Revision ID: 025_add_saved_parlay_inscription_credits_flag
Revises: 024_add_user_leaderboard_visibility
Create Date: 2025-12-30
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "025_add_saved_parlay_inscription_credits_flag"
down_revision = "024_add_user_leaderboard_visibility"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "saved_parlays",
        sa.Column("inscription_credits_consumed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("saved_parlays", "inscription_credits_consumed")




