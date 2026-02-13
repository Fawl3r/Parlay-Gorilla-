"""Add normalized_name to apisports_teams for DB-backed team name lookup.

Revision ID: 050_add_apisports_teams_normalized_name
Revises: 049_add_scheduler_job_runs
Create Date: 2026-02-13

Enables find_team_id_by_name(sport, normalized_name) without in-memory only mapping.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "050_add_apisports_teams_normalized_name"
down_revision = "049_add_scheduler_job_runs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "apisports_teams",
        sa.Column("normalized_name", sa.String(256), nullable=True),
    )
    op.create_index(
        "idx_apisports_teams_sport_normalized_name",
        "apisports_teams",
        ["sport", "normalized_name"],
    )


def downgrade() -> None:
    op.drop_index("idx_apisports_teams_sport_normalized_name", table_name="apisports_teams")
    op.drop_column("apisports_teams", "normalized_name")
