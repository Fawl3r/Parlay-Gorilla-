"""Add live scores and scraper tracking to games table.

Revision ID: 037_add_live_scores_to_games
Revises: 036_merge_migration_heads
Create Date: 2026-01-XX
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "037_add_live_scores_to_games"
down_revision = "036_merge_migration_heads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from sqlalchemy import inspect
    
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_columns = {col["name"]: col for col in inspector.get_columns("games")}
    existing_indexes = [idx["name"] for idx in inspector.get_indexes("games")]
    
    # Add score and status tracking columns (idempotent)
    if "home_score" not in existing_columns:
        op.add_column("games", sa.Column("home_score", sa.Integer(), nullable=True))
    if "away_score" not in existing_columns:
        op.add_column("games", sa.Column("away_score", sa.Integer(), nullable=True))
    if "period" not in existing_columns:
        op.add_column("games", sa.Column("period", sa.String(), nullable=True))
    if "clock" not in existing_columns:
        op.add_column("games", sa.Column("clock", sa.String(), nullable=True))
    if "last_scraped_at" not in existing_columns:
        op.add_column("games", sa.Column("last_scraped_at", sa.DateTime(timezone=True), nullable=True))
    if "data_source" not in existing_columns:
        op.add_column("games", sa.Column("data_source", sa.String(), nullable=True))
    if "is_stale" not in existing_columns:
        op.add_column("games", sa.Column("is_stale", sa.Boolean(), server_default=sa.text("false"), nullable=False))
    if "external_game_key" not in existing_columns:
        op.add_column("games", sa.Column("external_game_key", sa.String(), nullable=True))
    
    # Create indexes (idempotent)
    if "idx_games_status_start_time" not in existing_indexes:
        op.create_index("idx_games_status_start_time", "games", ["status", "start_time"])
    if "idx_games_external_game_key" not in existing_indexes:
        # Check for unique constraint first
        existing_constraints = [con["name"] for con in inspector.get_unique_constraints("games")]
        if "idx_games_external_game_key" not in existing_constraints:
            try:
                op.create_index("idx_games_external_game_key", "games", ["external_game_key"], unique=True)
            except Exception:
                # If unique constraint fails (duplicate keys), create non-unique index
                op.create_index("idx_games_external_game_key", "games", ["external_game_key"], unique=False)
    if "idx_games_stale_scraped" not in existing_indexes:
        op.create_index("idx_games_stale_scraped", "games", ["is_stale", "last_scraped_at"])


def downgrade() -> None:
    op.drop_index("idx_games_stale_scraped", table_name="games")
    op.drop_index("idx_games_external_game_key", table_name="games")
    op.drop_index("idx_games_status_start_time", table_name="games")
    op.drop_column("games", "external_game_key")
    op.drop_column("games", "is_stale")
    op.drop_column("games", "data_source")
    op.drop_column("games", "last_scraped_at")
    op.drop_column("games", "clock")
    op.drop_column("games", "period")
    op.drop_column("games", "away_score")
    op.drop_column("games", "home_score")
