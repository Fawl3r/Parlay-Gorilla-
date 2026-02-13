"""Add apisports_injury_entries and scheduler_job_runs.run_stats.

Revision ID: 051_add_injury_entries_and_job_run_stats
Revises: 050_add_apisports_teams_normalized_name
Create Date: 2026-02-13

- apisports_injury_entries: per-player injury rows (player_name, status, etc.)
- scheduler_job_runs.run_stats: JSON for injuries_provider_calls, injuries_records_written, injuries_teams_covered
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "051_add_injury_entries_and_job_run_stats"
down_revision = "050_add_apisports_teams_normalized_name"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    is_sqlite = conn.dialect.name == "sqlite"

    # run_stats on scheduler_job_runs (JSON; Postgres uses JSONB via model)
    op.add_column(
        "scheduler_job_runs",
        sa.Column("run_stats", sa.JSON(), nullable=True),
    )
    if is_sqlite:
        return

    # Per-player injury entries (Postgres only)
    op.create_table(
        "apisports_injury_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("sport", sa.String(32), nullable=False),
        sa.Column("league_id", sa.Integer(), nullable=True),
        sa.Column("apisports_team_id", sa.Integer(), nullable=False),
        sa.Column("apisports_player_id", sa.Integer(), nullable=True),
        sa.Column("player_name", sa.String(256), nullable=False),
        sa.Column("status", sa.String(64), nullable=False),
        sa.Column("injury_type", sa.String(128), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("reported_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(32), nullable=False, server_default="apisports"),
        sa.Column("raw_payload", postgresql.JSONB(), nullable=True),
    )
    op.create_index("ix_apisports_injury_entries_sport", "apisports_injury_entries", ["sport"])
    op.create_index("ix_apisports_injury_entries_apisports_team_id", "apisports_injury_entries", ["apisports_team_id"])
    op.create_index("ix_apisports_injury_entries_fetched_at", "apisports_injury_entries", ["fetched_at"])
    op.create_index(
        "idx_injury_entries_sport_team_fetched",
        "apisports_injury_entries",
        ["sport", "apisports_team_id", "fetched_at"],
    )



def downgrade() -> None:
    conn = op.get_bind()
    op.drop_column("scheduler_job_runs", "run_stats")
    if conn.dialect.name == "sqlite":
        return
    op.drop_index("idx_injury_entries_sport_team_fetched", table_name="apisports_injury_entries")
    op.drop_index("ix_apisports_injury_entries_fetched_at", table_name="apisports_injury_entries")
    op.drop_index("ix_apisports_injury_entries_apisports_team_id", table_name="apisports_injury_entries")
    op.drop_index("ix_apisports_injury_entries_sport", table_name="apisports_injury_entries")
    op.drop_table("apisports_injury_entries")
