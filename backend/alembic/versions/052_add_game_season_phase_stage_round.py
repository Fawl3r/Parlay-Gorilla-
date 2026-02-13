"""Add season_phase, stage, round to games for postseason detection.

Revision ID: 052_add_game_season_phase_stage_round
Revises: 051_add_injury_entries_and_job_run_stats
Create Date: 2026-02-13

- season_phase: "preseason" | "regular" | "postseason" (provider-driven)
- stage: provider stage text (e.g. Playoffs, Wildcard)
- round: provider round label
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "052_add_game_season_phase_stage_round"
down_revision = "051_add_injury_entries_and_job_run_stats"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("games", sa.Column("season_phase", sa.String(), nullable=True))
    op.add_column("games", sa.Column("stage", sa.String(), nullable=True))
    op.add_column("games", sa.Column("round", sa.String(), nullable=True))
    op.create_index(
        "idx_games_sport_season_phase",
        "games",
        ["sport", "season_phase"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_games_sport_season_phase", table_name="games")
    op.drop_column("games", "round")
    op.drop_column("games", "stage")
    op.drop_column("games", "season_phase")
