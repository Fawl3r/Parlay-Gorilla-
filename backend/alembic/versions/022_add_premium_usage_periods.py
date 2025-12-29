"""Add premium rolling-period usage counters to users.

Revision ID: 022_add_premium_usage_periods
Revises: 021_add_saved_parlay_results
Create Date: 2025-12-29
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "022_add_premium_usage_periods"
down_revision = "021_add_saved_parlay_results"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("premium_custom_builder_used", sa.Integer(), server_default=sa.text("0"), nullable=False),
    )
    op.add_column("users", sa.Column("premium_custom_builder_period_start", sa.DateTime(timezone=True), nullable=True))

    op.add_column(
        "users",
        sa.Column("premium_inscriptions_used", sa.Integer(), server_default=sa.text("0"), nullable=False),
    )
    op.add_column("users", sa.Column("premium_inscriptions_period_start", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "premium_inscriptions_period_start")
    op.drop_column("users", "premium_inscriptions_used")
    op.drop_column("users", "premium_custom_builder_period_start")
    op.drop_column("users", "premium_custom_builder_used")


