"""Add API-Sports team catalog and roster cache tables.

Revision ID: 045_add_apisports_team_and_rosters
Revises: 044_apisports_quota_per_sport
Create Date: 2026-01-30

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "045_add_apisports_team_and_rosters"
down_revision = "044_apisports_quota_per_sport"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        # API-Sports tables use PostgreSQL JSONB; skip on SQLite so upgrade completes.
        return

    # API-Sports team catalog (per sport/league/season)
    op.create_table(
        "apisports_teams",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("sport", sa.String(32), nullable=False),
        sa.Column("league_id", sa.Integer, nullable=True),
        sa.Column("team_id", sa.Integer, nullable=False),
        sa.Column("season", sa.String(16), nullable=True),
        sa.Column("name", sa.String(256), nullable=True),
        sa.Column("payload_json", postgresql.JSONB, nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("last_fetched_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("stale_after_seconds", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_apisports_teams_sport", "apisports_teams", ["sport"])
    op.create_index("ix_apisports_teams_league_id", "apisports_teams", ["league_id"])
    op.create_index("ix_apisports_teams_team_id", "apisports_teams", ["team_id"])
    op.create_index("ix_apisports_teams_season", "apisports_teams", ["season"])
    op.create_index("idx_apisports_teams_sport_team", "apisports_teams", ["sport", "team_id"])
    op.create_index("idx_apisports_teams_sport_league_season", "apisports_teams", ["sport", "league_id", "season"])
    op.create_index("idx_apisports_teams_sport_team_season", "apisports_teams", ["sport", "team_id", "season"], unique=True)

    # API-Sports team rosters (players per team/season)
    op.create_table(
        "apisports_team_rosters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("sport", sa.String(32), nullable=False),
        sa.Column("team_id", sa.Integer, nullable=False),
        sa.Column("season", sa.String(16), nullable=False),
        sa.Column("payload_json", postgresql.JSONB, nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("last_fetched_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("stale_after_seconds", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_apisports_team_rosters_sport", "apisports_team_rosters", ["sport"])
    op.create_index("ix_apisports_team_rosters_team_id", "apisports_team_rosters", ["team_id"])
    op.create_index("ix_apisports_team_rosters_season", "apisports_team_rosters", ["season"])
    op.create_index("idx_apisports_rosters_sport_team", "apisports_team_rosters", ["sport", "team_id"])
    op.create_index("idx_apisports_rosters_sport_team_season", "apisports_team_rosters", ["sport", "team_id", "season"], unique=True)


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    op.drop_index("idx_apisports_rosters_sport_team_season", table_name="apisports_team_rosters")
    op.drop_index("idx_apisports_rosters_sport_team", table_name="apisports_team_rosters")
    op.drop_index("ix_apisports_team_rosters_season", table_name="apisports_team_rosters")
    op.drop_index("ix_apisports_team_rosters_team_id", table_name="apisports_team_rosters")
    op.drop_index("ix_apisports_team_rosters_sport", table_name="apisports_team_rosters")
    op.drop_table("apisports_team_rosters")

    op.drop_index("idx_apisports_teams_sport_team_season", table_name="apisports_teams")
    op.drop_index("idx_apisports_teams_sport_league_season", table_name="apisports_teams")
    op.drop_index("idx_apisports_teams_sport_team", table_name="apisports_teams")
    op.drop_index("ix_apisports_teams_season", table_name="apisports_teams")
    op.drop_index("ix_apisports_teams_team_id", table_name="apisports_teams")
    op.drop_index("ix_apisports_teams_league_id", table_name="apisports_teams")
    op.drop_index("ix_apisports_teams_sport", table_name="apisports_teams")
    op.drop_table("apisports_teams")
