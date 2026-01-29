"""Add API-Sports cache tables and quota usage (DB-first, 100 req/day).

Revision ID: 042_add_apisports_tables
Revises: 041_create_system_heartbeats
Create Date: 2026-01-28

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "042_add_apisports_tables"
down_revision = "041_create_system_heartbeats"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        # API-Sports tables use PostgreSQL JSONB; skip on SQLite so upgrade completes.
        return
    # API-Sports fixtures cache
    op.create_table(
        "apisports_fixtures",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("sport", sa.String(32), nullable=False),
        sa.Column("league_id", sa.Integer, nullable=True),
        sa.Column("fixture_id", sa.Integer, nullable=True),
        sa.Column("date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("home_team_id", sa.Integer, nullable=True),
        sa.Column("away_team_id", sa.Integer, nullable=True),
        sa.Column("payload_json", postgresql.JSONB, nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("last_fetched_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("stale_after_seconds", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_apisports_fixtures_sport", "apisports_fixtures", ["sport"])
    op.create_index("ix_apisports_fixtures_league_id", "apisports_fixtures", ["league_id"])
    op.create_index("ix_apisports_fixtures_fixture_id", "apisports_fixtures", ["fixture_id"])
    op.create_index("ix_apisports_fixtures_date", "apisports_fixtures", ["date"])
    op.create_index("idx_apisports_fixtures_sport_date", "apisports_fixtures", ["sport", "date"])
    op.create_index("idx_apisports_fixtures_sport_fixture_id", "apisports_fixtures", ["sport", "fixture_id"])
    op.create_index("idx_apisports_fixtures_sport_league", "apisports_fixtures", ["sport", "league_id"])

    # API-Sports results
    op.create_table(
        "apisports_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("sport", sa.String(32), nullable=False),
        sa.Column("league_id", sa.Integer, nullable=True),
        sa.Column("fixture_id", sa.Integer, nullable=False),
        sa.Column("home_team_id", sa.Integer, nullable=True),
        sa.Column("away_team_id", sa.Integer, nullable=True),
        sa.Column("home_score", sa.Integer, nullable=True),
        sa.Column("away_score", sa.Integer, nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload_json", postgresql.JSONB, nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("last_fetched_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_apisports_results_sport", "apisports_results", ["sport"])
    op.create_index("ix_apisports_results_fixture_id", "apisports_results", ["fixture_id"])
    op.create_index("idx_apisports_results_sport_fixture", "apisports_results", ["sport", "fixture_id"], unique=True)
    op.create_index("idx_apisports_results_sport_date", "apisports_results", ["sport", "finished_at"])

    # API-Sports team stats
    op.create_table(
        "apisports_team_stats",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("sport", sa.String(32), nullable=False),
        sa.Column("league_id", sa.Integer, nullable=True),
        sa.Column("team_id", sa.Integer, nullable=False),
        sa.Column("season", sa.String(16), nullable=True),
        sa.Column("payload_json", postgresql.JSONB, nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("last_fetched_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("stale_after_seconds", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_apisports_team_stats_sport", "apisports_team_stats", ["sport"])
    op.create_index("ix_apisports_team_stats_team_id", "apisports_team_stats", ["team_id"])
    op.create_index("idx_apisports_team_stats_sport_team", "apisports_team_stats", ["sport", "team_id"])
    op.create_index("idx_apisports_team_stats_sport_league", "apisports_team_stats", ["sport", "league_id"])

    # API-Sports standings
    op.create_table(
        "apisports_standings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("sport", sa.String(32), nullable=False),
        sa.Column("league_id", sa.Integer, nullable=False),
        sa.Column("season", sa.String(16), nullable=True),
        sa.Column("payload_json", postgresql.JSONB, nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("last_fetched_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("stale_after_seconds", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_apisports_standings_sport", "apisports_standings", ["sport"])
    op.create_index("ix_apisports_standings_league_id", "apisports_standings", ["league_id"])
    op.create_index("idx_apisports_standings_sport_league", "apisports_standings", ["sport", "league_id"])

    # API-Sports injuries
    op.create_table(
        "apisports_injuries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("sport", sa.String(32), nullable=False),
        sa.Column("team_id", sa.Integer, nullable=True),
        sa.Column("league_id", sa.Integer, nullable=True),
        sa.Column("payload_json", postgresql.JSONB, nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("last_fetched_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("stale_after_seconds", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_apisports_injuries_sport", "apisports_injuries", ["sport"])
    op.create_index("ix_apisports_injuries_team_id", "apisports_injuries", ["team_id"])
    op.create_index("idx_apisports_injuries_sport_team", "apisports_injuries", ["sport", "team_id"])

    # API-Sports derived features
    op.create_table(
        "apisports_features",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("sport", sa.String(32), nullable=False),
        sa.Column("team_id", sa.Integer, nullable=True),
        sa.Column("league_id", sa.Integer, nullable=True),
        sa.Column("season", sa.String(16), nullable=True),
        sa.Column("features_json", postgresql.JSONB, nullable=False),
        sa.Column("last_n_form_wins", sa.Integer, nullable=True),
        sa.Column("last_n_form_losses", sa.Integer, nullable=True),
        sa.Column("rest_days", sa.Integer, nullable=True),
        sa.Column("home_away_split_json", postgresql.JSONB, nullable=True),
        sa.Column("opponent_strength_proxy", sa.Float, nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_apisports_features_sport", "apisports_features", ["sport"])
    op.create_index("ix_apisports_features_team_id", "apisports_features", ["team_id"])
    op.create_index("idx_apisports_features_sport_team", "apisports_features", ["sport", "team_id"])
    op.create_index("idx_apisports_features_sport_league", "apisports_features", ["sport", "league_id"])

    # Quota usage (DB fallback when Redis unavailable)
    op.create_table(
        "api_quota_usage",
        sa.Column("date", sa.String(10), primary_key=True),
        sa.Column("used", sa.Integer, nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("api_quota_usage")
    op.drop_index("idx_apisports_features_sport_league", table_name="apisports_features")
    op.drop_index("idx_apisports_features_sport_team", table_name="apisports_features")
    op.drop_index("ix_apisports_features_team_id", table_name="apisports_features")
    op.drop_index("ix_apisports_features_sport", table_name="apisports_features")
    op.drop_table("apisports_features")
    op.drop_index("idx_apisports_injuries_sport_team", table_name="apisports_injuries")
    op.drop_index("ix_apisports_injuries_team_id", table_name="apisports_injuries")
    op.drop_index("ix_apisports_injuries_sport", table_name="apisports_injuries")
    op.drop_table("apisports_injuries")
    op.drop_index("idx_apisports_standings_sport_league", table_name="apisports_standings")
    op.drop_index("ix_apisports_standings_league_id", table_name="apisports_standings")
    op.drop_index("ix_apisports_standings_sport", table_name="apisports_standings")
    op.drop_table("apisports_standings")
    op.drop_index("idx_apisports_team_stats_sport_league", table_name="apisports_team_stats")
    op.drop_index("idx_apisports_team_stats_sport_team", table_name="apisports_team_stats")
    op.drop_index("ix_apisports_team_stats_team_id", table_name="apisports_team_stats")
    op.drop_index("ix_apisports_team_stats_sport", table_name="apisports_team_stats")
    op.drop_table("apisports_team_stats")
    op.drop_index("idx_apisports_results_sport_date", table_name="apisports_results")
    op.drop_index("idx_apisports_results_sport_fixture", table_name="apisports_results")
    op.drop_index("ix_apisports_results_fixture_id", table_name="apisports_results")
    op.drop_index("ix_apisports_results_sport", table_name="apisports_results")
    op.drop_table("apisports_results")
    op.drop_index("idx_apisports_fixtures_sport_league", table_name="apisports_fixtures")
    op.drop_index("idx_apisports_fixtures_sport_fixture_id", table_name="apisports_fixtures")
    op.drop_index("idx_apisports_fixtures_sport_date", table_name="apisports_fixtures")
    op.drop_index("ix_apisports_fixtures_date", table_name="apisports_fixtures")
    op.drop_index("ix_apisports_fixtures_fixture_id", table_name="apisports_fixtures")
    op.drop_index("ix_apisports_fixtures_league_id", table_name="apisports_fixtures")
    op.drop_index("ix_apisports_fixtures_sport", table_name="apisports_fixtures")
    op.drop_table("apisports_fixtures")
