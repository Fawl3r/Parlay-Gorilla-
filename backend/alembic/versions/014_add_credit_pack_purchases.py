"""Add credit_pack_purchases table for purchase-level credit pack idempotency.

Revision ID: 014_add_credit_pack_purchases
Revises: 013_add_user_account_number
Create Date: 2025-12-18
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "014_add_credit_pack_purchases"
down_revision = "013_add_user_account_number"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "credit_pack_purchases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("provider_order_id", sa.String(length=255), nullable=False),
        sa.Column("credit_pack_id", sa.String(length=50), nullable=False),
        sa.Column("credits_awarded", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="fulfilled"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("fulfilled_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("provider", "provider_order_id", name="uq_credit_pack_purchases_provider_order_id"),
    )

    op.create_index("ix_credit_pack_purchases_user_id", "credit_pack_purchases", ["user_id"])
    op.create_index("ix_credit_pack_purchases_provider", "credit_pack_purchases", ["provider"])
    op.create_index("ix_credit_pack_purchases_credit_pack_id", "credit_pack_purchases", ["credit_pack_id"])
    op.create_index("ix_credit_pack_purchases_status", "credit_pack_purchases", ["status"])
    op.create_index("ix_credit_pack_purchases_created_at", "credit_pack_purchases", ["created_at"])

    op.create_index(
        "idx_credit_pack_purchases_user_created_at",
        "credit_pack_purchases",
        ["user_id", "created_at"],
    )
    op.create_index(
        "idx_credit_pack_purchases_provider_created_at",
        "credit_pack_purchases",
        ["provider", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_credit_pack_purchases_provider_created_at", table_name="credit_pack_purchases")
    op.drop_index("idx_credit_pack_purchases_user_created_at", table_name="credit_pack_purchases")
    op.drop_index("ix_credit_pack_purchases_created_at", table_name="credit_pack_purchases")
    op.drop_index("ix_credit_pack_purchases_status", table_name="credit_pack_purchases")
    op.drop_index("ix_credit_pack_purchases_credit_pack_id", table_name="credit_pack_purchases")
    op.drop_index("ix_credit_pack_purchases_provider", table_name="credit_pack_purchases")
    op.drop_index("ix_credit_pack_purchases_user_id", table_name="credit_pack_purchases")
    op.drop_table("credit_pack_purchases")


