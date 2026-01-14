"""Merge Alembic heads: arcade points tables + weekly free limits.

Revision ID: 029_merge_arcade_points_and_weekly_free_limits
Revises: 028_add_arcade_points_tables, 7b6df811d1cc
Create Date: 2026-01-14
"""

from __future__ import annotations


# revision identifiers, used by Alembic.
revision = "029_merge_arcade_points_and_weekly_free_limits"
down_revision = ("028_add_arcade_points_tables", "7b6df811d1cc")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Merge-only revision (no schema changes).
    pass


def downgrade() -> None:
    # Merge-only revision (no schema changes).
    pass


