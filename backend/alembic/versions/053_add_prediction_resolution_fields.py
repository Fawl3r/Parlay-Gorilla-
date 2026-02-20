"""Add resolution and EV fields to model_predictions for closed-loop ML.

Revision ID: 053_add_prediction_resolution_fields
Revises: 052_add_game_season_phase_stage_round
Create Date: 2026-02-20

- resolved_at: when prediction was resolved
- result: win/loss (true/false) for resolved predictions
- expected_value: EV at prediction time
- implied_odds: decimal odds at prediction time
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "053_add_prediction_resolution_fields"
down_revision = "052_add_game_season_phase_stage_round"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("model_predictions", sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("model_predictions", sa.Column("result", sa.Boolean(), nullable=True))
    op.add_column("model_predictions", sa.Column("expected_value", sa.Float(), nullable=True))
    op.add_column("model_predictions", sa.Column("implied_odds", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("model_predictions", "implied_odds")
    op.drop_column("model_predictions", "expected_value")
    op.drop_column("model_predictions", "result")
    op.drop_column("model_predictions", "resolved_at")
