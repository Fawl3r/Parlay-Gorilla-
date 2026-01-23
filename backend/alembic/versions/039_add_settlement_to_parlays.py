"""Add settlement fields to parlays and saved_parlays tables.

Revision ID: 039_add_settlement_to_parlays
Revises: 038_create_parlay_legs_table
Create Date: 2026-01-XX
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "039_add_settlement_to_parlays"
down_revision = "038_create_parlay_legs_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add settlement fields to parlays table
    op.add_column("parlays", sa.Column("status", sa.String(), nullable=False, server_default="PENDING"))
    op.add_column("parlays", sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("parlays", sa.Column("public_alias", sa.String(), nullable=True))
    op.add_column("parlays", sa.Column("is_public", sa.Boolean(), server_default=sa.text("false"), nullable=False))
    
    # Add settlement fields to saved_parlays table
    op.add_column("saved_parlays", sa.Column("status", sa.String(), nullable=False, server_default="PENDING"))
    op.add_column("saved_parlays", sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("saved_parlays", sa.Column("public_alias", sa.String(), nullable=True))
    op.add_column("saved_parlays", sa.Column("is_public", sa.Boolean(), server_default=sa.text("false"), nullable=False))
    
    # Create indexes for settlement queries
    op.create_index("idx_parlays_status", "parlays", ["status"])
    op.create_index("idx_saved_parlays_status", "saved_parlays", ["status"])


def downgrade() -> None:
    op.drop_index("idx_saved_parlays_status", table_name="saved_parlays")
    op.drop_index("idx_parlays_status", table_name="parlays")
    op.drop_column("saved_parlays", "is_public")
    op.drop_column("saved_parlays", "public_alias")
    op.drop_column("saved_parlays", "settled_at")
    op.drop_column("saved_parlays", "status")
    op.drop_column("parlays", "is_public")
    op.drop_column("parlays", "public_alias")
    op.drop_column("parlays", "settled_at")
    op.drop_column("parlays", "status")
