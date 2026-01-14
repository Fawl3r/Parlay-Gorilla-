"""Add arcade_points_events and arcade_points_totals tables.

Revision ID: 028_add_arcade_points_tables
Revises: 027_add_parlay_fingerprint_to_verification_records
Create Date: 2025-01-15
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "028_add_arcade_points_tables"
down_revision = "027_add_parlay_fingerprint_to_verification_records"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Arcade points events (one row per awarded win)
    op.create_table(
        "arcade_points_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("saved_parlay_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("saved_parlay_result_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("num_legs", sa.Integer(), nullable=False),
        sa.Column("points_awarded", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["saved_parlay_id"], ["saved_parlays.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["saved_parlay_result_id"], ["saved_parlay_results.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("saved_parlay_result_id", name="unique_arcade_points_event_result"),
    )

    op.create_index(
        "idx_arcade_points_events_user_created", "arcade_points_events", ["user_id", "created_at"], unique=False
    )
    op.create_index("idx_arcade_points_events_created", "arcade_points_events", ["created_at"], unique=False)

    # Arcade points totals (per-user aggregate)
    op.create_table(
        "arcade_points_totals",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("total_points", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("total_qualifying_wins", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("last_win_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="unique_arcade_points_totals_user"),
    )

    op.create_index("idx_arcade_points_totals_points", "arcade_points_totals", ["total_points"], unique=False)
    op.create_index("idx_arcade_points_totals_last_win", "arcade_points_totals", ["last_win_at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_arcade_points_totals_last_win", table_name="arcade_points_totals")
    op.drop_index("idx_arcade_points_totals_points", table_name="arcade_points_totals")
    op.drop_table("arcade_points_totals")

    op.drop_index("idx_arcade_points_events_created", table_name="arcade_points_events")
    op.drop_index("idx_arcade_points_events_user_created", table_name="arcade_points_events")
    op.drop_table("arcade_points_events")

