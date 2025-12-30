"""Add leaderboard_visibility to users.

Revision ID: 024_add_user_leaderboard_visibility
Revises: 023_add_saved_parlay_inscription_quota_flag
Create Date: 2025-12-29
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "024_add_user_leaderboard_visibility"
down_revision = "023_add_saved_parlay_inscription_quota_flag"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "leaderboard_visibility",
            sa.String(length=20),
            server_default=sa.text("'public'"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "leaderboard_visibility")


