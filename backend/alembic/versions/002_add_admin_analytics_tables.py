"""Add admin and analytics tables

Revision ID: 002_add_admin_analytics_tables
Revises: 001_add_prediction_tracking
Create Date: 2024-12-05 14:00:00.000000

Creates tables for admin panel and analytics:
- Extends users table with role, plan, is_active
- app_events: Generic analytics events
- parlay_events: Parlay-specific analytics
- payments: Payment records (LemonSqueezy/Coinbase stub)
- subscriptions: Active subscription tracking
- feature_flags: Feature toggles
- system_logs: API and error logs
- admin_sessions: Admin login tracking
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_add_admin_analytics_tables'
down_revision: Union[str, None] = '001_add_prediction_tracking'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ===========================================
    # Extend users table with role, plan, is_active
    # ===========================================
    op.add_column('users', sa.Column('role', sa.String(), nullable=True, server_default='user'))
    op.add_column('users', sa.Column('plan', sa.String(), nullable=True, server_default='free'))
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'))
    
    # Update existing rows to have default values
    op.execute("UPDATE users SET role = 'user' WHERE role IS NULL")
    op.execute("UPDATE users SET plan = 'free' WHERE plan IS NULL")
    op.execute("UPDATE users SET is_active = true WHERE is_active IS NULL")
    
    # Make columns non-nullable after setting defaults
    op.alter_column('users', 'role', nullable=False)
    op.alter_column('users', 'plan', nullable=False)
    op.alter_column('users', 'is_active', nullable=False)
    
    # Create indexes for new user columns
    op.create_index('idx_user_role', 'users', ['role'])
    op.create_index('idx_user_plan', 'users', ['plan'])
    op.create_index('idx_user_is_active', 'users', ['is_active'])
    
    # ===========================================
    # Create app_events table
    # ===========================================
    op.create_table(
        'app_events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('session_id', sa.String(64), nullable=True),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('referrer', sa.Text(), nullable=True),
        sa.Column('page_url', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_app_events_type_date', 'app_events', ['event_type', 'created_at'])
    op.create_index('idx_app_events_user_date', 'app_events', ['user_id', 'created_at'])
    op.create_index('idx_app_events_session', 'app_events', ['session_id'])
    op.create_index('idx_app_events_created', 'app_events', ['created_at'])
    op.create_index('idx_app_events_metadata', 'app_events', ['metadata'], postgresql_using='gin')
    
    # ===========================================
    # Create parlay_events table
    # ===========================================
    op.create_table(
        'parlay_events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('session_id', sa.String(64), nullable=True),
        sa.Column('parlay_id', sa.UUID(), nullable=True),
        sa.Column('parlay_type', sa.String(20), nullable=False),
        sa.Column('sport_filters', postgresql.JSONB(), nullable=True),
        sa.Column('legs_count', sa.Integer(), nullable=False),
        sa.Column('expected_value', sa.Float(), nullable=True),
        sa.Column('combined_odds', sa.Float(), nullable=True),
        sa.Column('hit_probability', sa.Float(), nullable=True),
        sa.Column('legs_breakdown', postgresql.JSONB(), nullable=True),
        sa.Column('was_saved', sa.Boolean(), server_default='false'),
        sa.Column('was_shared', sa.Boolean(), server_default='false'),
        sa.Column('build_method', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_parlay_events_type_date', 'parlay_events', ['parlay_type', 'created_at'])
    op.create_index('idx_parlay_events_user', 'parlay_events', ['user_id', 'created_at'])
    op.create_index('idx_parlay_events_legs', 'parlay_events', ['legs_count'])
    op.create_index('idx_parlay_events_session', 'parlay_events', ['session_id'])
    op.create_index('idx_parlay_events_parlay_id', 'parlay_events', ['parlay_id'])
    
    # ===========================================
    # Create payments table
    # ===========================================
    op.create_table(
        'payments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='USD'),
        sa.Column('plan', sa.String(50), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('provider_payment_id', sa.String(255), nullable=True),
        sa.Column('provider_order_id', sa.String(255), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('provider_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_payments_user_date', 'payments', ['user_id', 'created_at'])
    op.create_index('idx_payments_status_date', 'payments', ['status', 'created_at'])
    op.create_index('idx_payments_provider_date', 'payments', ['provider', 'created_at'])
    op.create_index('idx_payments_plan', 'payments', ['plan'])
    op.create_index('idx_payments_provider_payment_id', 'payments', ['provider_payment_id'], unique=True)
    op.create_index('idx_payments_provider_order_id', 'payments', ['provider_order_id'])
    
    # ===========================================
    # Create subscriptions table
    # ===========================================
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('plan', sa.String(50), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('provider_subscription_id', sa.String(255), nullable=True),
        sa.Column('provider_customer_id', sa.String(255), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancel_at_period_end', sa.Boolean(), server_default='false'),
        sa.Column('cancellation_reason', sa.String(255), nullable=True),
        sa.Column('provider_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_subscriptions_user_status', 'subscriptions', ['user_id', 'status'])
    op.create_index('idx_subscriptions_status_date', 'subscriptions', ['status', 'created_at'])
    op.create_index('idx_subscriptions_plan', 'subscriptions', ['plan', 'status'])
    op.create_index('idx_subscriptions_period_end', 'subscriptions', ['current_period_end'])
    op.create_index('idx_subscriptions_provider_sub_id', 'subscriptions', ['provider_subscription_id'], unique=True)
    op.create_index('idx_subscriptions_provider_customer_id', 'subscriptions', ['provider_customer_id'])
    
    # ===========================================
    # Create feature_flags table
    # ===========================================
    op.create_table(
        'feature_flags',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('key', sa.String(100), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('targeting_rules', postgresql.JSONB(), nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_feature_flags_key', 'feature_flags', ['key'], unique=True)
    op.create_index('idx_feature_flags_enabled', 'feature_flags', ['enabled'])
    op.create_index('idx_feature_flags_category', 'feature_flags', ['category'])
    
    # Insert default feature flags
    op.execute("""
        INSERT INTO feature_flags (id, key, name, description, enabled, category) VALUES
        (gen_random_uuid(), 'upset_finder', 'Upset Finder', 'Enable the Gorilla Upset Finder feature', true, 'feature'),
        (gen_random_uuid(), 'high_leg_parlays', 'High Leg Parlays', 'Allow parlays with 15-20 legs', true, 'feature'),
        (gen_random_uuid(), 'beta_features', 'Beta Features', 'Early access to experimental features', false, 'beta'),
        (gen_random_uuid(), 'ai_analysis', 'AI Analysis', 'Enable AI-powered game analysis narratives', true, 'feature')
    """)
    
    # ===========================================
    # Create system_logs table
    # ===========================================
    op.create_table(
        'system_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('level', sa.String(20), nullable=False, server_default='info'),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('error_type', sa.String(255), nullable=True),
        sa.Column('stack_trace', sa.Text(), nullable=True),
        sa.Column('request_id', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_system_logs_source_level', 'system_logs', ['source', 'level'])
    op.create_index('idx_system_logs_source_date', 'system_logs', ['source', 'created_at'])
    op.create_index('idx_system_logs_level_date', 'system_logs', ['level', 'created_at'])
    op.create_index('idx_system_logs_created', 'system_logs', ['created_at'])
    op.create_index('idx_system_logs_request_id', 'system_logs', ['request_id'])
    
    # ===========================================
    # Create admin_sessions table
    # ===========================================
    op.create_table(
        'admin_sessions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('admin_id', sa.UUID(), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.String(10), server_default='true'),
        sa.ForeignKeyConstraint(['admin_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_admin_sessions_admin_date', 'admin_sessions', ['admin_id', 'created_at'])
    op.create_index('idx_admin_sessions_active', 'admin_sessions', ['is_active'])


def downgrade() -> None:
    # Drop admin_sessions
    op.drop_index('idx_admin_sessions_active', table_name='admin_sessions')
    op.drop_index('idx_admin_sessions_admin_date', table_name='admin_sessions')
    op.drop_table('admin_sessions')
    
    # Drop system_logs
    op.drop_index('idx_system_logs_request_id', table_name='system_logs')
    op.drop_index('idx_system_logs_created', table_name='system_logs')
    op.drop_index('idx_system_logs_level_date', table_name='system_logs')
    op.drop_index('idx_system_logs_source_date', table_name='system_logs')
    op.drop_index('idx_system_logs_source_level', table_name='system_logs')
    op.drop_table('system_logs')
    
    # Drop feature_flags
    op.drop_index('idx_feature_flags_category', table_name='feature_flags')
    op.drop_index('idx_feature_flags_enabled', table_name='feature_flags')
    op.drop_index('idx_feature_flags_key', table_name='feature_flags')
    op.drop_table('feature_flags')
    
    # Drop subscriptions
    op.drop_index('idx_subscriptions_provider_customer_id', table_name='subscriptions')
    op.drop_index('idx_subscriptions_provider_sub_id', table_name='subscriptions')
    op.drop_index('idx_subscriptions_period_end', table_name='subscriptions')
    op.drop_index('idx_subscriptions_plan', table_name='subscriptions')
    op.drop_index('idx_subscriptions_status_date', table_name='subscriptions')
    op.drop_index('idx_subscriptions_user_status', table_name='subscriptions')
    op.drop_table('subscriptions')
    
    # Drop payments
    op.drop_index('idx_payments_provider_order_id', table_name='payments')
    op.drop_index('idx_payments_provider_payment_id', table_name='payments')
    op.drop_index('idx_payments_plan', table_name='payments')
    op.drop_index('idx_payments_provider_date', table_name='payments')
    op.drop_index('idx_payments_status_date', table_name='payments')
    op.drop_index('idx_payments_user_date', table_name='payments')
    op.drop_table('payments')
    
    # Drop parlay_events
    op.drop_index('idx_parlay_events_parlay_id', table_name='parlay_events')
    op.drop_index('idx_parlay_events_session', table_name='parlay_events')
    op.drop_index('idx_parlay_events_legs', table_name='parlay_events')
    op.drop_index('idx_parlay_events_user', table_name='parlay_events')
    op.drop_index('idx_parlay_events_type_date', table_name='parlay_events')
    op.drop_table('parlay_events')
    
    # Drop app_events
    op.drop_index('idx_app_events_metadata', table_name='app_events')
    op.drop_index('idx_app_events_created', table_name='app_events')
    op.drop_index('idx_app_events_session', table_name='app_events')
    op.drop_index('idx_app_events_user_date', table_name='app_events')
    op.drop_index('idx_app_events_type_date', table_name='app_events')
    op.drop_table('app_events')
    
    # Remove user columns
    op.drop_index('idx_user_is_active', table_name='users')
    op.drop_index('idx_user_plan', table_name='users')
    op.drop_index('idx_user_role', table_name='users')
    op.drop_column('users', 'is_active')
    op.drop_column('users', 'plan')
    op.drop_column('users', 'role')

