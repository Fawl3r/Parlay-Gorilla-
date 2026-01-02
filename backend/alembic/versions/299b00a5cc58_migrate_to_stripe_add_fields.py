"""migrate_to_stripe_add_fields

Revision ID: 299b00a5cc58
Revises: 025_add_saved_parlay_inscription_credits_flag
Create Date: 2026-01-02 07:36:55.198166

This migration:
- Adds stripe_customer_id and stripe_subscription_id to users table
- Updates subscription_plans.provider from 'lemonsqueezy' to 'stripe' (data migration)
- Updates subscriptions.provider from 'lemonsqueezy' to 'stripe' (data migration)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '299b00a5cc58'
down_revision: Union[str, None] = '025_add_saved_parlay_inscription_credits_flag'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add Stripe fields to users table
    op.add_column('users', sa.Column('stripe_customer_id', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('stripe_subscription_id', sa.String(255), nullable=True))
    
    # Create indexes for Stripe fields
    op.create_index('ix_users_stripe_customer_id', 'users', ['stripe_customer_id'], unique=False)
    op.create_index('ix_users_stripe_subscription_id', 'users', ['stripe_subscription_id'], unique=False)
    
    # Data migration: Update subscription_plans.provider from 'lemonsqueezy' to 'stripe'
    # Note: This is a data migration. Actual price IDs should be updated via admin or script.
    op.execute(
        text("UPDATE subscription_plans SET provider = 'stripe' WHERE provider = 'lemonsqueezy'")
    )
    
    # Data migration: Update subscriptions.provider from 'lemonsqueezy' to 'stripe'
    op.execute(
        text("UPDATE subscriptions SET provider = 'stripe' WHERE provider = 'lemonsqueezy'")
    )


def downgrade() -> None:
    # Revert data migrations
    op.execute(
        text("UPDATE subscriptions SET provider = 'lemonsqueezy' WHERE provider = 'stripe'")
    )
    op.execute(
        text("UPDATE subscription_plans SET provider = 'lemonsqueezy' WHERE provider = 'stripe'")
    )
    
    # Remove indexes
    op.drop_index('ix_users_stripe_subscription_id', table_name='users')
    op.drop_index('ix_users_stripe_customer_id', table_name='users')
    
    # Remove Stripe fields from users table
    op.drop_column('users', 'stripe_subscription_id')
    op.drop_column('users', 'stripe_customer_id')
