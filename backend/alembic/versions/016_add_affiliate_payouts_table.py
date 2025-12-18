"""Add affiliate_payouts + affiliate_payout_commissions tables for payouts + tax ledger.

Revision ID: 016_add_affiliate_payouts_table
Revises: 015_add_push_subscriptions
Create Date: 2025-12-18
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "016_add_affiliate_payouts_table"
down_revision = "015_add_push_subscriptions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "affiliate_payouts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("affiliate_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("affiliates.id"), nullable=False),
        # Tax ledger (USD)
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="USD", nullable=False),
        sa.Column("payout_method", sa.String(length=50), nullable=False),
        sa.Column("tax_amount_usd", sa.Numeric(12, 2), nullable=True),
        # Tax ledger (crypto details)
        sa.Column("asset_symbol", sa.String(length=12), nullable=True),
        sa.Column("asset_amount", sa.Numeric(18, 6), nullable=True),
        sa.Column("asset_chain", sa.String(length=32), nullable=True),
        sa.Column("transaction_hash", sa.String(length=255), nullable=True),
        sa.Column("valuation_usd_per_asset", sa.Numeric(18, 8), nullable=True),
        sa.Column("valuation_source", sa.String(length=64), nullable=True),
        sa.Column("valuation_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valuation_raw", sa.Text(), nullable=True),
        # Recipient snapshot
        sa.Column("recipient_email", sa.String(length=255), nullable=False),
        sa.Column("recipient_name", sa.String(length=255), nullable=True),
        # Status + provider
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("provider_payout_id", sa.String(length=255), nullable=True),
        sa.Column("provider_response", sa.Text(), nullable=True),
        # Errors
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        # Notes
        sa.Column("notes", sa.Text(), nullable=True),
    )

    op.create_index("ix_affiliate_payouts_affiliate_id", "affiliate_payouts", ["affiliate_id"])
    op.create_index("ix_affiliate_payouts_payout_method", "affiliate_payouts", ["payout_method"])
    op.create_index("ix_affiliate_payouts_status", "affiliate_payouts", ["status"])
    op.create_index("ix_affiliate_payouts_created_at", "affiliate_payouts", ["created_at"])
    op.create_index("ix_affiliate_payouts_provider_payout_id", "affiliate_payouts", ["provider_payout_id"])

    op.create_index(
        "idx_payouts_affiliate_status",
        "affiliate_payouts",
        ["affiliate_id", "status"],
    )
    op.create_index(
        "idx_payouts_status_created",
        "affiliate_payouts",
        ["status", "created_at"],
    )
    op.create_index(
        "idx_payouts_provider_id",
        "affiliate_payouts",
        ["provider_payout_id"],
    )
    op.create_index(
        "idx_payouts_completed_at",
        "affiliate_payouts",
        ["completed_at"],
    )

    op.create_table(
        "affiliate_payout_commissions",
        sa.Column("payout_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("affiliate_payouts.id"), primary_key=True),
        sa.Column("commission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("affiliate_commissions.id"), primary_key=True),
    )

    op.create_index(
        "idx_payout_commissions_payout",
        "affiliate_payout_commissions",
        ["payout_id"],
    )
    op.create_index(
        "idx_payout_commissions_commission",
        "affiliate_payout_commissions",
        ["commission_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_payout_commissions_commission", table_name="affiliate_payout_commissions")
    op.drop_index("idx_payout_commissions_payout", table_name="affiliate_payout_commissions")
    op.drop_table("affiliate_payout_commissions")

    op.drop_index("idx_payouts_completed_at", table_name="affiliate_payouts")
    op.drop_index("idx_payouts_provider_id", table_name="affiliate_payouts")
    op.drop_index("idx_payouts_status_created", table_name="affiliate_payouts")
    op.drop_index("idx_payouts_affiliate_status", table_name="affiliate_payouts")

    op.drop_index("ix_affiliate_payouts_provider_payout_id", table_name="affiliate_payouts")
    op.drop_index("ix_affiliate_payouts_created_at", table_name="affiliate_payouts")
    op.drop_index("ix_affiliate_payouts_status", table_name="affiliate_payouts")
    op.drop_index("ix_affiliate_payouts_payout_method", table_name="affiliate_payouts")
    op.drop_index("ix_affiliate_payouts_affiliate_id", table_name="affiliate_payouts")
    op.drop_table("affiliate_payouts")


