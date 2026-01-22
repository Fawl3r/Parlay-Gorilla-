"""Merge Alembic heads: 029_merge_arcade_points_and_weekly_free_limits and 035_add_stats_platform_tables.

Revision ID: 036_merge_migration_heads
Revises: 029_merge_arcade_points_and_weekly_free_limits, 035_add_stats_platform_tables
Create Date: 2026-01-22
"""

from __future__ import annotations


# revision identifiers, used by Alembic.
revision = "036_merge_migration_heads"
down_revision = ("029_merge_arcade_points_and_weekly_free_limits", "035_add_stats_platform_tables")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Merge-only revision (no schema changes).
    # This merges the two migration heads:
    # - 029_merge_arcade_points_and_weekly_free_limits (from arcade points branch)
    # - 035_add_stats_platform_tables (from stats platform branch via 299b00a5cc58 -> 030 -> ... -> 035)
    pass


def downgrade() -> None:
    # Merge-only revision (no schema changes).
    pass
