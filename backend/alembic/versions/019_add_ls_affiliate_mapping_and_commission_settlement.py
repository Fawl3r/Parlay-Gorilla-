"""Add LemonSqueezy affiliate mapping + commission settlement provider.

Revision ID: 019_add_ls_affiliate_mapping_and_commission_settlement
Revises: 018_add_crypto_time_based_and_card_lifetime_plans
Create Date: 2025-12-19
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "019_add_ls_affiliate_mapping_and_commission_settlement"
down_revision = "018_add_crypto_time_based_and_card_lifetime_plans"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Affiliates: map our internal referral_code -> LemonSqueezy affiliate code (?aff=1234)
    op.add_column(
        "affiliates",
        sa.Column("lemonsqueezy_affiliate_code", sa.String(length=50), nullable=True),
    )
    op.create_index(
        "idx_affiliates_ls_affiliate_code",
        "affiliates",
        ["lemonsqueezy_affiliate_code"],
    )

    # Affiliate commissions: mark where payouts are settled
    op.add_column(
        "affiliate_commissions",
        sa.Column(
            "settlement_provider",
            sa.String(length=20),
            nullable=False,
            server_default="internal",
        ),
    )
    op.create_index(
        "idx_affiliate_commissions_settlement_provider",
        "affiliate_commissions",
        ["settlement_provider"],
    )

    # Remove server default after backfill.
    op.alter_column("affiliate_commissions", "settlement_provider", server_default=None)


def downgrade() -> None:
    op.drop_index("idx_affiliate_commissions_settlement_provider", table_name="affiliate_commissions")
    op.drop_column("affiliate_commissions", "settlement_provider")

    op.drop_index("idx_affiliates_ls_affiliate_code", table_name="affiliates")
    op.drop_column("affiliates", "lemonsqueezy_affiliate_code")


