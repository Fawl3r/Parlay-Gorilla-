"""Add parlay purchases table for pay-per-use model

Revision ID: 006_parlay_purchases
Revises: 005_add_live_games_and_drives
Create Date: 2024-12-08

This migration adds:
- parlay_purchases: Tracks one-time parlay purchases ($3 single, $5 multi)
- Adds one-time parlay plans to subscription_plans table
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_parlay_purchases'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create parlay_purchases table
    op.create_table(
        'parlay_purchases',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('payment_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('parlay_type', sa.String(20), nullable=False),  # single or multi
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, default='USD'),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('provider', sa.String(50), nullable=True),
        sa.Column('provider_checkout_id', sa.String(255), nullable=True),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('parlay_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_parlay_purchases_user_id', 'parlay_purchases', ['user_id'], unique=False)
    op.create_index('ix_parlay_purchases_status', 'parlay_purchases', ['status'], unique=False)
    op.create_index('ix_parlay_purchases_parlay_type', 'parlay_purchases', ['parlay_type'], unique=False)
    op.create_index('ix_parlay_purchases_provider_checkout_id', 'parlay_purchases', ['provider_checkout_id'], unique=False)
    op.create_index('ix_parlay_purchases_expires_at', 'parlay_purchases', ['expires_at'], unique=False)
    op.create_index('idx_parlay_purchases_user_status', 'parlay_purchases', ['user_id', 'status'], unique=False)
    op.create_index('idx_parlay_purchases_user_type_status', 'parlay_purchases', ['user_id', 'parlay_type', 'status'], unique=False)

    # Insert one-time parlay purchase plans
    op.execute("""
        INSERT INTO subscription_plans (
            id, code, name, description, price_cents, currency, billing_cycle, provider,
            is_active, is_featured, max_ai_parlays_per_day, can_use_custom_builder,
            can_use_upset_finder, can_use_multi_sport, can_save_parlays, ad_free, display_order
        ) VALUES
        -- Single-sport parlay one-time purchase ($3)
        (
            gen_random_uuid(), 'PG_SINGLE_PARLAY_ONETIME', 'Single Parlay',
            'Generate one AI parlay for a single sport. Valid for 24 hours.',
            300, 'USD', 'one_time', 'lemonsqueezy',
            true, false, 0, false, false, false, false, false, 10
        ),
        -- Multi-sport parlay one-time purchase ($5)
        (
            gen_random_uuid(), 'PG_MULTI_PARLAY_ONETIME', 'Multi-Sport Parlay',
            'Generate one AI parlay mixing multiple sports. Valid for 24 hours.',
            500, 'USD', 'one_time', 'lemonsqueezy',
            true, false, 0, false, false, true, false, false, 11
        )
        ON CONFLICT (code) DO UPDATE SET
            price_cents = EXCLUDED.price_cents,
            description = EXCLUDED.description,
            is_active = EXCLUDED.is_active
    """)


def downgrade() -> None:
    # Remove one-time parlay plans
    op.execute("""
        DELETE FROM subscription_plans 
        WHERE code IN ('PG_SINGLE_PARLAY_ONETIME', 'PG_MULTI_PARLAY_ONETIME')
    """)
    
    # Drop parlay_purchases table indexes
    op.drop_index('idx_parlay_purchases_user_type_status', table_name='parlay_purchases')
    op.drop_index('idx_parlay_purchases_user_status', table_name='parlay_purchases')
    op.drop_index('ix_parlay_purchases_expires_at', table_name='parlay_purchases')
    op.drop_index('ix_parlay_purchases_provider_checkout_id', table_name='parlay_purchases')
    op.drop_index('ix_parlay_purchases_parlay_type', table_name='parlay_purchases')
    op.drop_index('ix_parlay_purchases_status', table_name='parlay_purchases')
    op.drop_index('ix_parlay_purchases_user_id', table_name='parlay_purchases')
    
    # Drop parlay_purchases table
    op.drop_table('parlay_purchases')

