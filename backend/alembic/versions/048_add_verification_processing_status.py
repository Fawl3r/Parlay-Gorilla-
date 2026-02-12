"""Add processing status and processing_started_at for Pattern A verifier.

Revision ID: 048_add_verification_processing_status
Revises: 047_settlement_lock_and_game_status
Create Date: 2026-02-06

Allows verification_records.status = 'processing' and adds processing_started_at
for atomic claiming and stuck-job detection.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "048_add_verification_processing_status"
down_revision = "047_settlement_lock_and_game_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "verification_records",
        sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("verification_records", "processing_started_at")
