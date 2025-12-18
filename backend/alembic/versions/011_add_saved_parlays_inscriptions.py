"""Add saved_parlays table for user-saved parlays + Solana inscription metadata.

Revision ID: 011_add_saved_parlays_inscriptions
Revises: 010_update_hof_first_sub_rate
Create Date: 2025-12-18
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "011_add_saved_parlays_inscriptions"
down_revision = "010_update_hof_first_sub_rate"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "saved_parlays",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parlay_type", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("legs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("inscription_status", sa.String(length=20), server_default=sa.text("'none'"), nullable=False),
        sa.Column("inscription_hash", sa.String(length=64), nullable=True),
        sa.Column("inscription_tx", sa.String(length=128), nullable=True),
        sa.Column("inscription_error", sa.Text(), nullable=True),
        sa.Column("inscribed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Indexes requested by spec.
    op.create_index("idx_saved_parlays_user_created", "saved_parlays", ["user_id", "created_at"], unique=False)
    op.create_index("idx_saved_parlays_user_type", "saved_parlays", ["user_id", "parlay_type"], unique=False)
    op.create_index(
        "idx_saved_parlays_inscription_status", "saved_parlays", ["inscription_status"], unique=False
    )


def downgrade() -> None:
    op.drop_index("idx_saved_parlays_inscription_status", table_name="saved_parlays")
    op.drop_index("idx_saved_parlays_user_type", table_name="saved_parlays")
    op.drop_index("idx_saved_parlays_user_created", table_name="saved_parlays")
    op.drop_table("saved_parlays")



