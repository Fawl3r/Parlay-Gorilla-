"""Add stats platform v2 tables for immutable snapshots, canonical data, and derived features.

Revision ID: 035_add_stats_platform_tables
Revises: 034_add_watched_games
Create Date: 2026-01-XX
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "035_add_stats_platform_tables"
down_revision = "034_add_watched_games"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        # Stats platform v2 uses PostgreSQL JSONB; skip on SQLite so upgrade completes.
        return
    # 1. team_stats_snapshots - Immutable raw stats data
    op.create_table(
        "team_stats_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("team_name", sa.String, nullable=False),
        sa.Column("sport", sa.String, nullable=False),
        sa.Column("season", sa.String, nullable=False),
        sa.Column("source", sa.String, nullable=False),  # "db_seed", "api_espn", "api_sportsradar", etc.
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("raw_json", postgresql.JSONB, nullable=False),
        sa.Column("hash", sa.String(64), nullable=False),  # SHA256 hash for deduplication
    )
    op.create_index("ix_team_stats_snapshots_team_name", "team_stats_snapshots", ["team_name"])
    op.create_index("ix_team_stats_snapshots_sport", "team_stats_snapshots", ["sport"])
    op.create_index("ix_team_stats_snapshots_season", "team_stats_snapshots", ["season"])
    op.create_index("ix_team_stats_snapshots_collected_at", "team_stats_snapshots", ["collected_at"])
    op.create_index("ix_team_stats_snapshots_hash", "team_stats_snapshots", ["hash"])
    op.create_index(
        "idx_team_stats_snapshots_team_sport_season",
        "team_stats_snapshots",
        ["team_name", "sport", "season", "collected_at"],
    )
    
    # 2. injury_snapshots - Immutable raw injury data
    op.create_table(
        "injury_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("team_name", sa.String, nullable=False),
        sa.Column("sport", sa.String, nullable=False),
        sa.Column("season", sa.String, nullable=False),
        sa.Column("source", sa.String, nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("raw_json", postgresql.JSONB, nullable=False),
        sa.Column("hash", sa.String(64), nullable=False),  # SHA256 hash for deduplication
    )
    op.create_index("ix_injury_snapshots_team_name", "injury_snapshots", ["team_name"])
    op.create_index("ix_injury_snapshots_sport", "injury_snapshots", ["sport"])
    op.create_index("ix_injury_snapshots_season", "injury_snapshots", ["season"])
    op.create_index("ix_injury_snapshots_collected_at", "injury_snapshots", ["collected_at"])
    op.create_index("ix_injury_snapshots_hash", "injury_snapshots", ["hash"])
    op.create_index(
        "idx_injury_snapshots_team_sport_season",
        "injury_snapshots",
        ["team_name", "sport", "season", "collected_at"],
    )
    
    # 3. team_stats_current - Canonical normalized current stats
    op.create_table(
        "team_stats_current",
        sa.Column("team_name", sa.String, nullable=False),
        sa.Column("sport", sa.String, nullable=False),
        sa.Column("season", sa.String, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("metrics_json", postgresql.JSONB, nullable=False),
        sa.PrimaryKeyConstraint("team_name", "sport", "season"),
    )
    op.create_index("ix_team_stats_current_team_name", "team_stats_current", ["team_name"])
    op.create_index("ix_team_stats_current_sport", "team_stats_current", ["sport"])
    op.create_index("ix_team_stats_current_season", "team_stats_current", ["season"])
    op.create_index("ix_team_stats_current_updated_at", "team_stats_current", ["updated_at"])
    op.create_index(
        "idx_team_stats_current_team_sport_season",
        "team_stats_current",
        ["team_name", "sport", "season"],
        unique=True,
    )
    
    # 4. injury_current - Canonical normalized current injuries
    op.create_table(
        "injury_current",
        sa.Column("team_name", sa.String, nullable=False),
        sa.Column("sport", sa.String, nullable=False),
        sa.Column("season", sa.String, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("injury_json", postgresql.JSONB, nullable=False),
        sa.PrimaryKeyConstraint("team_name", "sport", "season"),
    )
    op.create_index("ix_injury_current_team_name", "injury_current", ["team_name"])
    op.create_index("ix_injury_current_sport", "injury_current", ["sport"])
    op.create_index("ix_injury_current_season", "injury_current", ["season"])
    op.create_index("ix_injury_current_updated_at", "injury_current", ["updated_at"])
    op.create_index(
        "idx_injury_current_team_sport_season",
        "injury_current",
        ["team_name", "sport", "season"],
        unique=True,
    )
    
    # 5. team_features_current - Derived bettor-grade features
    op.create_table(
        "team_features_current",
        sa.Column("team_name", sa.String, nullable=False),
        sa.Column("sport", sa.String, nullable=False),
        sa.Column("season", sa.String, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("features_json", postgresql.JSONB, nullable=False),
        sa.Column("data_quality_json", postgresql.JSONB, nullable=False),
        sa.PrimaryKeyConstraint("team_name", "sport", "season"),
    )
    op.create_index("ix_team_features_current_team_name", "team_features_current", ["team_name"])
    op.create_index("ix_team_features_current_sport", "team_features_current", ["sport"])
    op.create_index("ix_team_features_current_season", "team_features_current", ["season"])
    op.create_index("ix_team_features_current_updated_at", "team_features_current", ["updated_at"])
    op.create_index(
        "idx_team_features_current_team_sport_season",
        "team_features_current",
        ["team_name", "sport", "season"],
        unique=True,
    )


def downgrade() -> None:
    # Drop in reverse order
    op.drop_index("idx_team_features_current_team_sport_season", table_name="team_features_current")
    op.drop_index("ix_team_features_current_updated_at", table_name="team_features_current")
    op.drop_index("ix_team_features_current_season", table_name="team_features_current")
    op.drop_index("ix_team_features_current_sport", table_name="team_features_current")
    op.drop_index("ix_team_features_current_team_name", table_name="team_features_current")
    op.drop_table("team_features_current")
    
    op.drop_index("idx_injury_current_team_sport_season", table_name="injury_current")
    op.drop_index("ix_injury_current_updated_at", table_name="injury_current")
    op.drop_index("ix_injury_current_season", table_name="injury_current")
    op.drop_index("ix_injury_current_sport", table_name="injury_current")
    op.drop_index("ix_injury_current_team_name", table_name="injury_current")
    op.drop_table("injury_current")
    
    op.drop_index("idx_team_stats_current_team_sport_season", table_name="team_stats_current")
    op.drop_index("ix_team_stats_current_updated_at", table_name="team_stats_current")
    op.drop_index("ix_team_stats_current_season", table_name="team_stats_current")
    op.drop_index("ix_team_stats_current_sport", table_name="team_stats_current")
    op.drop_index("ix_team_stats_current_team_name", table_name="team_stats_current")
    op.drop_table("team_stats_current")
    
    op.drop_index("idx_injury_snapshots_team_sport_season", table_name="injury_snapshots")
    op.drop_index("ix_injury_snapshots_hash", table_name="injury_snapshots")
    op.drop_index("ix_injury_snapshots_collected_at", table_name="injury_snapshots")
    op.drop_index("ix_injury_snapshots_season", table_name="injury_snapshots")
    op.drop_index("ix_injury_snapshots_sport", table_name="injury_snapshots")
    op.drop_index("ix_injury_snapshots_team_name", table_name="injury_snapshots")
    op.drop_table("injury_snapshots")
    
    op.drop_index("idx_team_stats_snapshots_team_sport_season", table_name="team_stats_snapshots")
    op.drop_index("ix_team_stats_snapshots_hash", table_name="team_stats_snapshots")
    op.drop_index("ix_team_stats_snapshots_collected_at", table_name="team_stats_snapshots")
    op.drop_index("ix_team_stats_snapshots_season", table_name="team_stats_snapshots")
    op.drop_index("ix_team_stats_snapshots_sport", table_name="team_stats_snapshots")
    op.drop_index("ix_team_stats_snapshots_team_name", table_name="team_stats_snapshots")
    op.drop_table("team_stats_snapshots")
