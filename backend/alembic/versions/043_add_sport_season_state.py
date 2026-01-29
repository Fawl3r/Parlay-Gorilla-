"""Add sport_season_state table for cached season state per sport.

Revision ID: 043_add_sport_season_state
Revises: 042_add_apisports_tables
Create Date: 2026-01-29

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "043_add_sport_season_state"
down_revision = "042_add_apisports_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sport_season_state",
        sa.Column("sport", sa.String(16), primary_key=True),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("computed_at_utc", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("recent_final_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("near_scheduled_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("post_scheduled_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )


def downgrade() -> None:
    op.drop_table("sport_season_state")
