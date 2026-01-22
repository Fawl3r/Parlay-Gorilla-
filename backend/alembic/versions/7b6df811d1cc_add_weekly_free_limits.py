"""Add weekly free limits with rolling 7-day window

Revision ID: 7b6df811d1cc
Revises: 027_add_parlay_fingerprint_to_verification_records
Create Date: 2025-01-XX

This migration:
- Adds first_usage_at timestamp column to usage_limits table for rolling 7-day window tracking
- Migrates existing daily records to weekly format by setting first_usage_at to created_at
- Changes free limits from daily (3 per day) to weekly (5 per rolling 7-day period)
- Adds index on (user_id, first_usage_at) for efficient window queries
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '7b6df811d1cc'
down_revision = '027_add_parlay_fingerprint_to_verification_records'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add first_usage_at column (nullable initially for migration)
    # Use IF NOT EXISTS to make migration idempotent - safe to re-run
    op.execute("""
        ALTER TABLE usage_limits
        ADD COLUMN IF NOT EXISTS first_usage_at TIMESTAMPTZ
    """)
    
    # Migrate existing records: set first_usage_at to created_at for existing records
    # This preserves the start of their usage window
    # Safe to re-run: WHERE clause ensures we only update NULL values
    op.execute("""
        UPDATE usage_limits
        SET first_usage_at = created_at
        WHERE first_usage_at IS NULL
    """)
    
    # Now make the column non-nullable (all existing records have been migrated)
    # Check if column is already non-nullable before altering
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Get column info to check if it's already non-nullable
    existing_columns = {col["name"]: col for col in inspector.get_columns("usage_limits")}
    first_usage_col = existing_columns.get("first_usage_at")
    
    # Only alter if column exists and is still nullable
    if first_usage_col and first_usage_col.get("nullable", True):
        op.alter_column(
            'usage_limits',
            'first_usage_at',
            nullable=False,
            server_default=sa.text('now()')
        )
    
    # Add index for efficient queries on user_id + first_usage_at
    # Check if index already exists before creating
    existing_indexes = [idx["name"] for idx in inspector.get_indexes("usage_limits")]
    if 'idx_usage_limits_user_first_usage' not in existing_indexes:
        op.create_index(
            'idx_usage_limits_user_first_usage',
            'usage_limits',
            ['user_id', 'first_usage_at'],
            unique=False
        )


def downgrade() -> None:
    # Remove index
    op.drop_index('idx_usage_limits_user_first_usage', table_name='usage_limits')
    
    # Remove column
    op.drop_column('usage_limits', 'first_usage_at')
