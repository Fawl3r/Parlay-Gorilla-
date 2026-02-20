"""Add result_enum to model_predictions and calibration_bins table.

Revision ID: 056_result_enum_and_calibration_bins
Revises: 055_alpha_engine_tables
Create Date: 2026-02-20

- result_enum: WIN/LOSS/PUSH/VOID for resolved predictions
- calibration_bins: bin_low, bin_high, empirical_hit_rate, sample_count for lightweight calibration
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "056_result_enum_and_calibration_bins"
down_revision = "055_alpha_engine_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("model_predictions", sa.Column("result_enum", sa.String(), nullable=True))

    op.create_table(
        "calibration_bins",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("bin_index", sa.Integer(), nullable=False),
        sa.Column("bin_low", sa.Float(), nullable=False),
        sa.Column("bin_high", sa.Float(), nullable=False),
        sa.Column("empirical_hit_rate", sa.Float(), nullable=False),
        sa.Column("sample_count", sa.Integer(), nullable=False),
        sa.Column("trained_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_calibration_bins_trained", "calibration_bins", ["trained_at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_calibration_bins_trained", table_name="calibration_bins")
    op.drop_table("calibration_bins")
    op.drop_column("model_predictions", "result_enum")
