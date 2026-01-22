"""Add performance indexes for faster queries.

Revision ID: 033_add_performance_indexes
Revises: 032_add_analysis_page_views
Create Date: 2026-01-XX
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "033_add_performance_indexes"
down_revision = "032_add_analysis_page_views"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Composite index for games table: (sport, start_time, status)
    # Used by scheduler._generate_upcoming_analyses() and odds_fetcher queries
    op.create_index(
        "idx_games_sport_time_status",
        "games",
        ["sport", "start_time", "status"],
    )
    
    # Composite index for analysis_page_views table: (league, view_bucket_date)
    # Used by TrafficRanker.get_top_game_ids() for traffic ranking
    op.create_index(
        "idx_views_league_date",
        "analysis_page_views",
        ["league", "view_bucket_date"],
    )


def downgrade() -> None:
    op.drop_index("idx_views_league_date", table_name="analysis_page_views")
    op.drop_index("idx_games_sport_time_status", table_name="games")
