"""Add premium AI parlay monthly tracking to users

Revision ID: 012_add_premium_ai_parlays_monthly
Revises: 011_add_saved_parlays_inscriptions
Create Date: 2025-01-XX
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "012_add_premium_ai_parlays_monthly"
down_revision = "011_add_saved_parlays_inscriptions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("premium_ai_parlays_used", sa.Integer(), nullable=False, server_default="0"))
    op.add_column(
        "users",
        sa.Column("premium_ai_parlays_period_start", postgresql.TIMESTAMP(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "premium_ai_parlays_period_start")
    op.drop_column("users", "premium_ai_parlays_used")


