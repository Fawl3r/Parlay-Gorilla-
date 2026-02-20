"""Add alpha_meta_state columns for ops/alpha-engine-status.

Revision ID: 057_alpha_meta_state_status
Revises: 056_result_enum_and_calibration_bins
Create Date: 2026-02-20

- system_state, last_feature_discovery_at, last_alpha_research_at,
  last_experiment_eval_at, last_error, last_error_at, correlation_id
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "057_alpha_meta_state_status"
down_revision = "056_result_enum_and_calibration_bins"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("alpha_meta_state", sa.Column("system_state", sa.String(), nullable=True))
    op.add_column("alpha_meta_state", sa.Column("last_feature_discovery_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("alpha_meta_state", sa.Column("last_alpha_research_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("alpha_meta_state", sa.Column("last_experiment_eval_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("alpha_meta_state", sa.Column("last_error", sa.String(), nullable=True))
    op.add_column("alpha_meta_state", sa.Column("last_error_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("alpha_meta_state", sa.Column("correlation_id", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("alpha_meta_state", "correlation_id")
    op.drop_column("alpha_meta_state", "last_error_at")
    op.drop_column("alpha_meta_state", "last_error")
    op.drop_column("alpha_meta_state", "last_experiment_eval_at")
    op.drop_column("alpha_meta_state", "last_alpha_research_at")
    op.drop_column("alpha_meta_state", "last_feature_discovery_at")
    op.drop_column("alpha_meta_state", "system_state")
