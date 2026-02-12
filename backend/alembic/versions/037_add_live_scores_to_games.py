"""Add live scores and scraper tracking to games table.

Revision ID: 037_add_live_scores_to_games
Revises: 036_merge_migration_heads
Create Date: 2026-01-XX
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "037_add_live_scores_to_games"
down_revision = "036_merge_migration_heads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from sqlalchemy import inspect
    from sqlalchemy.exc import ProgrammingError

    conn = op.get_bind()
    inspector = inspect(conn)
    dialect_name = conn.dialect.name

    def column_exists(table_name: str, column_name: str) -> bool:
        if dialect_name == "postgresql":
            result = conn.execute(sa.text(
                "SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_schema = 'public' AND table_name = :tbl AND column_name = :col)"
            ), {"tbl": table_name, "col": column_name})
            return result.scalar()
        cols = [c["name"] for c in inspector.get_columns(table_name)]
        return column_name in cols

    def index_exists(index_name: str) -> bool:
        if dialect_name == "postgresql":
            result = conn.execute(sa.text(
                "SELECT EXISTS (SELECT FROM pg_indexes WHERE schemaname = 'public' AND indexname = :idx_name)"
            ), {"idx_name": index_name})
            return result.scalar()
        for tbl in inspector.get_table_names():
            for idx in inspector.get_indexes(tbl):
                if idx["name"] == index_name:
                    return True
        return False
    
    # Add score and status tracking columns (idempotent)
    if not column_exists("games", "home_score"):
        op.add_column("games", sa.Column("home_score", sa.Integer(), nullable=True))
    if not column_exists("games", "away_score"):
        op.add_column("games", sa.Column("away_score", sa.Integer(), nullable=True))
    if not column_exists("games", "period"):
        op.add_column("games", sa.Column("period", sa.String(), nullable=True))
    if not column_exists("games", "clock"):
        op.add_column("games", sa.Column("clock", sa.String(), nullable=True))
    if not column_exists("games", "last_scraped_at"):
        op.add_column("games", sa.Column("last_scraped_at", sa.DateTime(timezone=True), nullable=True))
    if not column_exists("games", "data_source"):
        op.add_column("games", sa.Column("data_source", sa.String(), nullable=True))
    if not column_exists("games", "is_stale"):
        op.add_column("games", sa.Column("is_stale", sa.Boolean(), server_default=sa.text("false"), nullable=False))
    if not column_exists("games", "external_game_key"):
        try:
            op.add_column("games", sa.Column("external_game_key", sa.String(), nullable=True))
        except ProgrammingError as e:
            error_str = str(e).lower()
            if "already exists" not in error_str and "duplicate" not in error_str:
                raise
    
    # Create indexes (idempotent)
    if not index_exists("idx_games_status_start_time"):
        try:
            op.create_index("idx_games_status_start_time", "games", ["status", "start_time"])
        except ProgrammingError as e:
            if "already exists" not in str(e).lower():
                raise
    
    if not index_exists("idx_games_external_game_key"):
        try:
            # Try unique index first
            op.create_index("idx_games_external_game_key", "games", ["external_game_key"], unique=True)
        except ProgrammingError:
            # If unique constraint fails (duplicate keys), create non-unique index
            try:
                op.create_index("idx_games_external_game_key", "games", ["external_game_key"], unique=False)
            except ProgrammingError as e:
                if "already exists" not in str(e).lower():
                    raise
    
    if not index_exists("idx_games_stale_scraped"):
        try:
            op.create_index("idx_games_stale_scraped", "games", ["is_stale", "last_scraped_at"])
        except ProgrammingError as e:
            if "already exists" not in str(e).lower():
                raise


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
