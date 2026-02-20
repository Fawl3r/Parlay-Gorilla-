"""Institutional adaptive learning: strategy contributions, weights, regime, model health.

Revision ID: 054_institutional_adaptive_learning_tables
Revises: 053_add_prediction_resolution_fields
Create Date: 2026-02-20

- strategy_contributions: per-prediction strategy_name, weight, contribution_value
- strategy_weights: strategy_name, weight, updated_at (learned weights)
- model_predictions: strategy_components (JSON), market_regime (str)
- model_health_state: model_state, health_score, updated_at, etc.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "054_institutional_adaptive_learning_tables"
down_revision = "053_add_prediction_resolution_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # strategy_weights: persisted learned weights (strategy_name, weight, updated_at)
    op.create_table(
        "strategy_weights",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("strategy_name", sa.String(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_strategy_weights_name", "strategy_weights", ["strategy_name"], unique=True)

    # strategy_contributions: per-prediction breakdown
    op.create_table(
        "strategy_contributions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("prediction_id", sa.UUID(), nullable=False),
        sa.Column("strategy_name", sa.String(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("contribution_value", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["prediction_id"], ["model_predictions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_strategy_contributions_prediction", "strategy_contributions", ["prediction_id"])

    # model_predictions: strategy_components (JSON), market_regime
    op.add_column("model_predictions", sa.Column("strategy_components", sa.JSON(), nullable=True))
    op.add_column("model_predictions", sa.Column("market_regime", sa.String(), nullable=True))
    op.add_column("model_predictions", sa.Column("correlation_id", sa.String(), nullable=True))
    op.create_index("idx_predictions_correlation_id", "model_predictions", ["correlation_id"])

    # model_health_state: GREEN/YELLOW/RED, health_score, last_rl_update, etc.
    op.create_table(
        "model_health_state",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("model_state", sa.String(), nullable=False, server_default="GREEN"),
        sa.Column("health_score", sa.Float(), nullable=True),
        sa.Column("rolling_roi", sa.Float(), nullable=True),
        sa.Column("last_rl_update_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("calibration_version", sa.String(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("model_health_state")
    op.drop_index("idx_predictions_correlation_id", table_name="model_predictions")
    op.drop_column("model_predictions", "correlation_id")
    op.drop_column("model_predictions", "market_regime")
    op.drop_column("model_predictions", "strategy_components")
    op.drop_index("idx_strategy_contributions_prediction", table_name="strategy_contributions")
    op.drop_table("strategy_contributions")
    op.drop_index("idx_strategy_weights_name", table_name="strategy_weights")
    op.drop_table("strategy_weights")
