"""Add analysis page views tracking table.

Revision ID: 032_add_analysis_page_views
Revises: 031_add_fetch_budget_tracking
Create Date: 2026-01-XX
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "032_add_analysis_page_views"
down_revision = "031_add_fetch_budget_tracking"
branch_labels = None
depends_on = None


def _is_postgres() -> bool:
    bind = op.get_bind()
    return bind is not None and bind.dialect.name == "postgresql"


def upgrade() -> None:
    op.create_table(
        "analysis_page_views",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("game_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("league", sa.String, nullable=False),
        sa.Column("slug", sa.String, nullable=False),
        sa.Column("view_bucket_date", sa.Date, nullable=False),
        sa.Column("views", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("unique_visitors", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["analysis_id"], ["game_analyses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_analysis_page_views_analysis_id", "analysis_page_views", ["analysis_id"])
    op.create_index("ix_analysis_page_views_game_id", "analysis_page_views", ["game_id"])
    op.create_index("ix_analysis_page_views_league", "analysis_page_views", ["league"])
    op.create_index("ix_analysis_page_views_slug", "analysis_page_views", ["slug"])
    op.create_index("ix_analysis_page_views_view_bucket_date", "analysis_page_views", ["view_bucket_date"])
    op.create_index(
        "uq_analysis_page_views_analysis_date",
        "analysis_page_views",
        ["analysis_id", "view_bucket_date"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_analysis_page_views_analysis_date", table_name="analysis_page_views")
    op.drop_index("ix_analysis_page_views_view_bucket_date", table_name="analysis_page_views")
    op.drop_index("ix_analysis_page_views_slug", table_name="analysis_page_views")
    op.drop_index("ix_analysis_page_views_league", table_name="analysis_page_views")
    op.drop_index("ix_analysis_page_views_game_id", table_name="analysis_page_views")
    op.drop_index("ix_analysis_page_views_analysis_id", table_name="analysis_page_views")
    op.drop_table("analysis_page_views")
