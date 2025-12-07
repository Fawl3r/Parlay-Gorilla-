"""Add subscription and billing system tables

Revision ID: 003_subscription_billing
Revises: 002_add_admin_analytics_tables
Create Date: 2024-12-06

This migration adds:
- subscription_plans: Stores available subscription plans with provider product IDs
- usage_limits: Tracks daily feature usage (e.g., free parlay limit)
- payment_events: Stores webhook payloads for auditing
- Adds is_lifetime column to subscriptions table
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_subscription_billing'
down_revision = '002_add_admin_analytics_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create subscription_plans table
    op.create_table(
        'subscription_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price_cents', sa.Integer(), nullable=False, default=0),
        sa.Column('currency', sa.String(3), nullable=False, default='USD'),
        sa.Column('billing_cycle', sa.String(20), nullable=False, default='monthly'),
        sa.Column('provider', sa.String(20), nullable=False),
        sa.Column('provider_product_id', sa.String(255), nullable=True),
        sa.Column('provider_price_id', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_featured', sa.Boolean(), nullable=False, default=False),
        sa.Column('max_ai_parlays_per_day', sa.Integer(), nullable=True, default=1),
        sa.Column('can_use_custom_builder', sa.Boolean(), nullable=False, default=False),
        sa.Column('can_use_upset_finder', sa.Boolean(), nullable=False, default=False),
        sa.Column('can_use_multi_sport', sa.Boolean(), nullable=False, default=False),
        sa.Column('can_save_parlays', sa.Boolean(), nullable=False, default=False),
        sa.Column('ad_free', sa.Boolean(), nullable=False, default=False),
        sa.Column('display_order', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_subscription_plans_code', 'subscription_plans', ['code'], unique=True)
    op.create_index('ix_subscription_plans_provider', 'subscription_plans', ['provider'], unique=False)
    op.create_index('ix_subscription_plans_is_active', 'subscription_plans', ['is_active'], unique=False)

    # Create usage_limits table
    op.create_table(
        'usage_limits',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('free_parlays_generated', sa.Integer(), nullable=False, default=0),
        sa.Column('custom_parlays_built', sa.Integer(), nullable=False, default=0),
        sa.Column('upset_finder_queries', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'date', name='uq_usage_limits_user_date')
    )
    op.create_index('ix_usage_limits_user_id', 'usage_limits', ['user_id'], unique=False)
    op.create_index('ix_usage_limits_date', 'usage_limits', ['date'], unique=False)
    op.create_index('idx_usage_limits_user_date', 'usage_limits', ['user_id', 'date'], unique=False)

    # Create payment_events table
    op.create_table(
        'payment_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('provider', sa.String(20), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('event_id', sa.String(255), nullable=True),
        sa.Column('raw_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('provider_customer_id', sa.String(255), nullable=True),
        sa.Column('provider_subscription_id', sa.String(255), nullable=True),
        sa.Column('provider_order_id', sa.String(255), nullable=True),
        sa.Column('processed', sa.String(20), nullable=False, default='pending'),
        sa.Column('processing_error', sa.Text(), nullable=True),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_payment_events_user_id', 'payment_events', ['user_id'], unique=False)
    op.create_index('ix_payment_events_provider', 'payment_events', ['provider'], unique=False)
    op.create_index('ix_payment_events_event_type', 'payment_events', ['event_type'], unique=False)
    op.create_index('ix_payment_events_event_id', 'payment_events', ['event_id'], unique=True)
    op.create_index('idx_payment_events_provider_type', 'payment_events', ['provider', 'event_type'], unique=False)
    op.create_index('idx_payment_events_provider_customer', 'payment_events', ['provider', 'provider_customer_id'], unique=False)
    op.create_index('idx_payment_events_processed', 'payment_events', ['processed', 'created_at'], unique=False)

    # Add is_lifetime column to subscriptions table
    op.add_column('subscriptions', sa.Column('is_lifetime', sa.Boolean(), nullable=False, server_default='false'))

    # Insert default subscription plans
    op.execute("""
        INSERT INTO subscription_plans (
            id, code, name, description, price_cents, currency, billing_cycle, provider,
            is_active, is_featured, max_ai_parlays_per_day, can_use_custom_builder,
            can_use_upset_finder, can_use_multi_sport, can_save_parlays, ad_free, display_order
        ) VALUES
        -- Free tier (no payment)
        (
            gen_random_uuid(), 'PG_FREE', 'Free', 
            'Get started with Parlay Gorilla. 1 AI parlay per day with full access to game analysis.',
            0, 'USD', 'monthly', 'lemonsqueezy',
            true, false, 1, false, false, false, false, false, 0
        ),
        -- Monthly Premium via LemonSqueezy
        (
            gen_random_uuid(), 'PG_PREMIUM_MONTHLY', 'Gorilla Premium Monthly',
            'Unlimited AI parlays, custom builder, upset finder, and more. Billed monthly.',
            999, 'USD', 'monthly', 'lemonsqueezy',
            true, true, -1, true, true, true, true, true, 1
        ),
        -- Annual Premium via LemonSqueezy
        (
            gen_random_uuid(), 'PG_PREMIUM_ANNUAL', 'Gorilla Premium Annual',
            'Save 17% with annual billing. All premium features included.',
            9999, 'USD', 'annual', 'lemonsqueezy',
            true, false, -1, true, true, true, true, true, 2
        ),
        -- Lifetime via Coinbase Commerce (crypto)
        (
            gen_random_uuid(), 'PG_LIFETIME', 'Gorilla Lifetime',
            'Pay once, access forever. Pay with crypto via Coinbase Commerce.',
            19999, 'USD', 'lifetime', 'coinbase',
            true, false, -1, true, true, true, true, true, 3
        )
    """)


def downgrade() -> None:
    # Remove is_lifetime column from subscriptions
    op.drop_column('subscriptions', 'is_lifetime')
    
    # Drop payment_events table
    op.drop_index('idx_payment_events_processed', table_name='payment_events')
    op.drop_index('idx_payment_events_provider_customer', table_name='payment_events')
    op.drop_index('idx_payment_events_provider_type', table_name='payment_events')
    op.drop_index('ix_payment_events_event_id', table_name='payment_events')
    op.drop_index('ix_payment_events_event_type', table_name='payment_events')
    op.drop_index('ix_payment_events_provider', table_name='payment_events')
    op.drop_index('ix_payment_events_user_id', table_name='payment_events')
    op.drop_table('payment_events')
    
    # Drop usage_limits table
    op.drop_index('idx_usage_limits_user_date', table_name='usage_limits')
    op.drop_index('ix_usage_limits_date', table_name='usage_limits')
    op.drop_index('ix_usage_limits_user_id', table_name='usage_limits')
    op.drop_table('usage_limits')
    
    # Drop subscription_plans table
    op.drop_index('ix_subscription_plans_is_active', table_name='subscription_plans')
    op.drop_index('ix_subscription_plans_provider', table_name='subscription_plans')
    op.drop_index('ix_subscription_plans_code', table_name='subscription_plans')
    op.drop_table('subscription_plans')

