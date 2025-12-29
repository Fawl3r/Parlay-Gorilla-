"""Add saved_parlay_results table for tracking outcomes of saved parlays.

Revision ID: 021_add_saved_parlay_results
Revises: 020_case_insensitive_email_uniqueness
Create Date: 2025-12-28
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "021_add_saved_parlay_results"
down_revision = "020_case_insensitive_email_uniqueness"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "saved_parlay_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("saved_parlay_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parlay_type", sa.String(length=20), nullable=False),
        sa.Column("num_legs", sa.Integer(), nullable=False),
        sa.Column("hit", sa.Boolean(), nullable=True),
        sa.Column("legs_hit", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("legs_missed", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("leg_results", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["saved_parlay_id"], ["saved_parlays.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("idx_saved_parlay_results_saved", "saved_parlay_results", ["saved_parlay_id"], unique=False)
    op.create_index(
        "idx_saved_parlay_results_user_created", "saved_parlay_results", ["user_id", "created_at"], unique=False
    )
    op.create_index("idx_saved_parlay_results_hit", "saved_parlay_results", ["hit"], unique=False)
    op.create_index("idx_saved_parlay_results_type", "saved_parlay_results", ["parlay_type"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_saved_parlay_results_type", table_name="saved_parlay_results")
    op.drop_index("idx_saved_parlay_results_hit", table_name="saved_parlay_results")
    op.drop_index("idx_saved_parlay_results_user_created", table_name="saved_parlay_results")
    op.drop_index("idx_saved_parlay_results_saved", table_name="saved_parlay_results")
    op.drop_table("saved_parlay_results")


