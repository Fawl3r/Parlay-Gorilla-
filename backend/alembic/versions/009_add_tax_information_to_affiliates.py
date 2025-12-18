"""Add tax information fields to affiliates table

Revision ID: 009_tax_info_affiliates
Revises: 008_affiliate_credits
Create Date: 2024-12-11

This migration adds tax information fields required for US tax compliance:
- W-9 form fields (for US affiliates earning $600+)
- W-8BEN fields (for international affiliates)
- Tax form status tracking
- Address and tax ID information
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from decimal import Decimal

# revision identifiers, used by Alembic.
revision = '009_tax_info_affiliates'
down_revision = '008_affiliate_credits'
branch_labels = None
depends_on = None


def upgrade():
    # Add tax information columns to affiliates table
    op.add_column('affiliates', sa.Column('tax_form_type', sa.String(20), nullable=True))
    op.add_column('affiliates', sa.Column('tax_form_status', sa.String(20), server_default='not_submitted', nullable=False))
    op.add_column('affiliates', sa.Column('tax_form_submitted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('affiliates', sa.Column('tax_form_verified_at', sa.DateTime(timezone=True), nullable=True))
    
    # Legal/Business Information
    op.add_column('affiliates', sa.Column('legal_name', sa.String(255), nullable=True))
    op.add_column('affiliates', sa.Column('business_name', sa.String(255), nullable=True))
    op.add_column('affiliates', sa.Column('tax_classification', sa.String(50), nullable=True))
    
    # Address fields
    op.add_column('affiliates', sa.Column('tax_address_street', sa.String(255), nullable=True))
    op.add_column('affiliates', sa.Column('tax_address_city', sa.String(100), nullable=True))
    op.add_column('affiliates', sa.Column('tax_address_state', sa.String(50), nullable=True))
    op.add_column('affiliates', sa.Column('tax_address_zip', sa.String(20), nullable=True))
    op.add_column('affiliates', sa.Column('tax_address_country', sa.String(100), server_default='US', nullable=True))
    
    # Tax ID numbers
    op.add_column('affiliates', sa.Column('tax_id_number', sa.String(50), nullable=True))
    op.add_column('affiliates', sa.Column('tax_id_type', sa.String(20), nullable=True))
    
    # International tax (W-8BEN)
    op.add_column('affiliates', sa.Column('country_of_residence', sa.String(100), nullable=True))
    op.add_column('affiliates', sa.Column('foreign_tax_id', sa.String(50), nullable=True))
    
    # Tax form signature tracking
    op.add_column('affiliates', sa.Column('tax_form_signed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('affiliates', sa.Column('tax_form_ip_address', sa.String(45), nullable=True))
    
    # Minimum payout threshold (default $600 for US)
    op.add_column('affiliates', sa.Column('tax_form_required_threshold', sa.Numeric(10, 2), server_default='600.00', nullable=False))
    
    # Create index on tax_form_status for quick queries
    op.create_index('idx_affiliates_tax_form_status', 'affiliates', ['tax_form_status'])


def downgrade():
    op.drop_index('idx_affiliates_tax_form_status', table_name='affiliates')
    op.drop_column('affiliates', 'tax_form_required_threshold')
    op.drop_column('affiliates', 'tax_form_ip_address')
    op.drop_column('affiliates', 'tax_form_signed_at')
    op.drop_column('affiliates', 'foreign_tax_id')
    op.drop_column('affiliates', 'country_of_residence')
    op.drop_column('affiliates', 'tax_id_type')
    op.drop_column('affiliates', 'tax_id_number')
    op.drop_column('affiliates', 'tax_address_country')
    op.drop_column('affiliates', 'tax_address_zip')
    op.drop_column('affiliates', 'tax_address_state')
    op.drop_column('affiliates', 'tax_address_city')
    op.drop_column('affiliates', 'tax_address_street')
    op.drop_column('affiliates', 'tax_classification')
    op.drop_column('affiliates', 'business_name')
    op.drop_column('affiliates', 'legal_name')
    op.drop_column('affiliates', 'tax_form_verified_at')
    op.drop_column('affiliates', 'tax_form_submitted_at')
    op.drop_column('affiliates', 'tax_form_status')
    op.drop_column('affiliates', 'tax_form_type')




