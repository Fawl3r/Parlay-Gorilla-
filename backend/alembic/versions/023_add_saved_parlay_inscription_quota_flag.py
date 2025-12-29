"""Add inscription_quota_consumed flag to saved_parlays.

Revision ID: 023_add_saved_parlay_inscription_quota_flag
Revises: 022_add_premium_usage_periods
Create Date: 2025-12-29
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "023_add_saved_parlay_inscription_quota_flag"
down_revision = "022_add_premium_usage_periods"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "saved_parlays",
        sa.Column("inscription_quota_consumed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("saved_parlays", "inscription_quota_consumed")


