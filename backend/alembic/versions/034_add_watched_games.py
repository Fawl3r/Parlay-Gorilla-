"""Add watched games table for user watchlist.

Revision ID: 034_add_watched_games
Revises: 033_add_performance_indexes
Create Date: 2026-01-XX
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "034_add_watched_games"
down_revision = "033_add_performance_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "watched_games",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String, nullable=False),
        sa.Column("game_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_watched_games_user_id", "watched_games", ["user_id"])
    op.create_index("ix_watched_games_game_id", "watched_games", ["game_id"])
    op.create_index(
        "idx_watched_game_user_game",
        "watched_games",
        ["user_id", "game_id"],
        unique=True,
    )
    op.create_index(
        "idx_watched_game_user_created",
        "watched_games",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_watched_game_user_created", table_name="watched_games")
    op.drop_index("idx_watched_game_user_game", table_name="watched_games")
    op.drop_index("ix_watched_games_game_id", table_name="watched_games")
    op.drop_index("ix_watched_games_user_id", table_name="watched_games")
    op.drop_table("watched_games")
