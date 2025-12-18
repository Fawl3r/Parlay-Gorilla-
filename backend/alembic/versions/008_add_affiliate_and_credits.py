"""Add affiliate program and credits system

Revision ID: 008_affiliate_credits
Revises: 007_add_admin_and_billing
Create Date: 2024-12-11

This migration adds:
1. New user fields for free parlays, subscriptions, and credits
2. Affiliate table for affiliate accounts
3. AffiliateClick table for click tracking
4. AffiliateReferral table for referral attribution
5. AffiliateCommission table for commission tracking
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008_affiliate_credits'
down_revision = '006_parlay_purchases'
branch_labels = None
depends_on = None


def upgrade():
    # ==========================================================================
    # 1. Add new columns to users table
    # ==========================================================================
    
    # Free tier / trial access
    op.add_column('users', sa.Column('free_parlays_total', sa.Integer(), nullable=False, server_default='2'))
    op.add_column('users', sa.Column('free_parlays_used', sa.Integer(), nullable=False, server_default='0'))
    
    # Subscription status (extended fields)
    op.add_column('users', sa.Column('subscription_plan', sa.String(50), nullable=True))
    op.add_column('users', sa.Column('subscription_status', sa.String(20), nullable=False, server_default='none'))
    op.add_column('users', sa.Column('subscription_renewal_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('subscription_last_billed_at', sa.DateTime(timezone=True), nullable=True))
    
    # Daily parlay usage tracking
    op.add_column('users', sa.Column('daily_parlays_used', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('daily_parlays_usage_date', sa.Date(), nullable=True))
    
    # Credit balance
    op.add_column('users', sa.Column('credit_balance', sa.Integer(), nullable=False, server_default='0'))
    
    # Affiliate references
    op.add_column('users', sa.Column('affiliate_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('users', sa.Column('referred_by_affiliate_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Add indexes
    op.create_index('idx_user_subscription_status', 'users', ['subscription_status'])
    op.create_index('idx_user_referred_by', 'users', ['referred_by_affiliate_id'])
    
    # ==========================================================================
    # 2. Create affiliates table
    # ==========================================================================
    
    op.create_table(
        'affiliates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, unique=True),
        sa.Column('referral_code', sa.String(20), nullable=False, unique=True),
        sa.Column('tier', sa.String(20), nullable=False, server_default='rookie'),
        sa.Column('commission_rate_sub_first', sa.Numeric(5, 4), nullable=False, server_default='0.20'),
        sa.Column('commission_rate_sub_recurring', sa.Numeric(5, 4), nullable=False, server_default='0.00'),
        sa.Column('commission_rate_credits', sa.Numeric(5, 4), nullable=False, server_default='0.20'),
        sa.Column('total_referred_revenue', sa.Numeric(12, 2), nullable=False, server_default='0.00'),
        sa.Column('total_commission_earned', sa.Numeric(12, 2), nullable=False, server_default='0.00'),
        sa.Column('total_commission_paid', sa.Numeric(12, 2), nullable=False, server_default='0.00'),
        sa.Column('total_clicks', sa.Numeric(10, 0), nullable=False, server_default='0'),
        sa.Column('total_referrals', sa.Numeric(10, 0), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_approved', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('payout_email', sa.String(255), nullable=True),
        sa.Column('payout_method', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    op.create_index('idx_affiliates_user_id', 'affiliates', ['user_id'])
    op.create_index('idx_affiliates_referral_code', 'affiliates', ['referral_code'])
    op.create_index('idx_affiliates_tier', 'affiliates', ['tier'])
    op.create_index('idx_affiliates_is_active', 'affiliates', ['is_active'])
    
    # ==========================================================================
    # 3. Create affiliate_clicks table
    # ==========================================================================
    
    op.create_table(
        'affiliate_clicks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('affiliate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('affiliates.id'), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('referer_url', sa.Text(), nullable=True),
        sa.Column('landing_page', sa.Text(), nullable=True),
        sa.Column('utm_source', sa.String(255), nullable=True),
        sa.Column('utm_medium', sa.String(255), nullable=True),
        sa.Column('utm_campaign', sa.String(255), nullable=True),
        sa.Column('converted', sa.String(1), nullable=False, server_default='N'),
        sa.Column('converted_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('converted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    op.create_index('idx_affiliate_clicks_affiliate_id', 'affiliate_clicks', ['affiliate_id'])
    op.create_index('idx_affiliate_clicks_created_at', 'affiliate_clicks', ['created_at'])
    op.create_index('idx_affiliate_clicks_ip_address', 'affiliate_clicks', ['ip_address'])
    op.create_index('idx_affiliate_clicks_converted', 'affiliate_clicks', ['converted'])
    
    # ==========================================================================
    # 4. Create affiliate_referrals table
    # ==========================================================================
    
    op.create_table(
        'affiliate_referrals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('affiliate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('affiliates.id'), nullable=False),
        sa.Column('referred_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, unique=True),
        sa.Column('click_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('affiliate_clicks.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    op.create_index('idx_affiliate_referrals_affiliate_id', 'affiliate_referrals', ['affiliate_id'])
    op.create_index('idx_affiliate_referrals_referred_user_id', 'affiliate_referrals', ['referred_user_id'])
    op.create_index('idx_affiliate_referrals_created_at', 'affiliate_referrals', ['created_at'])
    
    # ==========================================================================
    # 5. Create affiliate_commissions table
    # ==========================================================================
    
    op.create_table(
        'affiliate_commissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('affiliate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('affiliates.id'), nullable=False),
        sa.Column('referred_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('sale_id', sa.String(255), nullable=False),
        sa.Column('sale_type', sa.String(20), nullable=False),
        sa.Column('base_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('commission_rate', sa.Numeric(5, 4), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='USD'),
        sa.Column('is_first_subscription_payment', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('subscription_plan', sa.String(50), nullable=True),
        sa.Column('credit_pack_id', sa.String(50), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('ready_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('payout_id', sa.String(255), nullable=True),
        sa.Column('payout_notes', sa.String(500), nullable=True),
    )
    
    op.create_index('idx_affiliate_commissions_affiliate_id', 'affiliate_commissions', ['affiliate_id'])
    op.create_index('idx_affiliate_commissions_referred_user_id', 'affiliate_commissions', ['referred_user_id'])
    op.create_index('idx_affiliate_commissions_sale_id', 'affiliate_commissions', ['sale_id'])
    op.create_index('idx_affiliate_commissions_status', 'affiliate_commissions', ['status'])
    op.create_index('idx_affiliate_commissions_ready_at', 'affiliate_commissions', ['ready_at'])
    op.create_index('idx_affiliate_commissions_sale_type', 'affiliate_commissions', ['sale_type'])
    
    # ==========================================================================
    # 6. Add foreign key for users.referred_by_affiliate_id
    # ==========================================================================
    
    op.create_foreign_key(
        'fk_users_referred_by_affiliate',
        'users', 'affiliates',
        ['referred_by_affiliate_id'], ['id']
    )


def downgrade():
    # Drop foreign key
    op.drop_constraint('fk_users_referred_by_affiliate', 'users', type_='foreignkey')
    
    # Drop tables in reverse order
    op.drop_table('affiliate_commissions')
    op.drop_table('affiliate_referrals')
    op.drop_table('affiliate_clicks')
    op.drop_table('affiliates')
    
    # Drop indexes
    op.drop_index('idx_user_subscription_status', 'users')
    op.drop_index('idx_user_referred_by', 'users')
    
    # Drop columns from users table
    op.drop_column('users', 'referred_by_affiliate_id')
    op.drop_column('users', 'affiliate_id')
    op.drop_column('users', 'credit_balance')
    op.drop_column('users', 'daily_parlays_usage_date')
    op.drop_column('users', 'daily_parlays_used')
    op.drop_column('users', 'subscription_last_billed_at')
    op.drop_column('users', 'subscription_renewal_date')
    op.drop_column('users', 'subscription_status')
    op.drop_column('users', 'subscription_plan')
    op.drop_column('users', 'free_parlays_used')
    op.drop_column('users', 'free_parlays_total')

