"""Add profile, badges, and verification system

Revision ID: 004_profile_badges_verification
Revises: 003_subscription_billing
Create Date: 2024-12-07

This migration adds:
- New columns to users table: email_verified, profile_completed, bio, timezone
- badges table: Badge definitions for achievement system
- user_badges table: Junction table for user's earned badges
- verification_tokens table: Secure tokens for email verification and password reset
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_profile_badges_verification'
down_revision = '003_subscription_billing'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ===========================================================================
    # Add new columns to users table
    # ===========================================================================
    
    # Add email_verified column with default False
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'))
    
    # Add profile_completed column with default False
    op.add_column('users', sa.Column('profile_completed', sa.Boolean(), nullable=False, server_default='false'))
    
    # Add bio column (nullable text)
    op.add_column('users', sa.Column('bio', sa.Text(), nullable=True))
    
    # Add timezone column (nullable string)
    op.add_column('users', sa.Column('timezone', sa.String(50), nullable=True))
    
    # Add indexes for new columns
    op.create_index('idx_user_email_verified', 'users', ['email_verified'])
    op.create_index('idx_user_profile_completed', 'users', ['profile_completed'])
    
    # ===========================================================================
    # Create badges table
    # ===========================================================================
    op.create_table(
        'badges',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('slug', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(100), nullable=True),
        sa.Column('requirement_type', sa.String(50), nullable=False),
        sa.Column('requirement_value', sa.Integer(), nullable=False, default=1),
        sa.Column('display_order', sa.Integer(), nullable=False, default=0),
        sa.Column('is_active', sa.String(1), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create unique constraint on slug
    op.create_index('idx_badge_slug', 'badges', ['slug'], unique=True)
    op.create_index('idx_badge_requirement_type', 'badges', ['requirement_type'])
    op.create_index('idx_badge_display_order', 'badges', ['display_order'])
    
    # ===========================================================================
    # Create user_badges table
    # ===========================================================================
    op.create_table(
        'user_badges',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('badge_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('unlocked_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['badge_id'], ['badges.id'], ondelete='CASCADE'),
    )
    
    # Create UNIQUE constraint to prevent duplicate badge awards
    op.create_unique_constraint('uq_user_badge', 'user_badges', ['user_id', 'badge_id'])
    
    # Create indexes
    op.create_index('idx_user_badge_user', 'user_badges', ['user_id'])
    op.create_index('idx_user_badge_badge', 'user_badges', ['badge_id'])
    op.create_index('idx_user_badge_unlocked', 'user_badges', ['unlocked_at'])
    
    # ===========================================================================
    # Create verification_tokens table
    # ===========================================================================
    op.create_table(
        'verification_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token_hash', sa.String(64), nullable=False),
        sa.Column('token_type', sa.String(20), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for efficient queries
    op.create_index('idx_verification_token_hash', 'verification_tokens', ['token_hash'])
    op.create_index('idx_verification_token_expires', 'verification_tokens', ['expires_at'])
    op.create_index('idx_verification_token_user_type', 'verification_tokens', ['user_id', 'token_type'])
    op.create_index('idx_verification_token_type', 'verification_tokens', ['token_type'])


def downgrade() -> None:
    # Drop verification_tokens table and indexes
    op.drop_index('idx_verification_token_type', table_name='verification_tokens')
    op.drop_index('idx_verification_token_user_type', table_name='verification_tokens')
    op.drop_index('idx_verification_token_expires', table_name='verification_tokens')
    op.drop_index('idx_verification_token_hash', table_name='verification_tokens')
    op.drop_table('verification_tokens')
    
    # Drop user_badges table and indexes
    op.drop_index('idx_user_badge_unlocked', table_name='user_badges')
    op.drop_index('idx_user_badge_badge', table_name='user_badges')
    op.drop_index('idx_user_badge_user', table_name='user_badges')
    op.drop_constraint('uq_user_badge', 'user_badges', type_='unique')
    op.drop_table('user_badges')
    
    # Drop badges table and indexes
    op.drop_index('idx_badge_display_order', table_name='badges')
    op.drop_index('idx_badge_requirement_type', table_name='badges')
    op.drop_index('idx_badge_slug', table_name='badges')
    op.drop_table('badges')
    
    # Remove columns from users table
    op.drop_index('idx_user_profile_completed', table_name='users')
    op.drop_index('idx_user_email_verified', table_name='users')
    op.drop_column('users', 'timezone')
    op.drop_column('users', 'bio')
    op.drop_column('users', 'profile_completed')
    op.drop_column('users', 'email_verified')

