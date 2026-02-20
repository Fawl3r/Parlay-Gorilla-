"""Alpha engine tables: alpha_features, experiments, strategy graph, decay log, meta state.

Revision ID: 055_alpha_engine_tables
Revises: 054_institutional_adaptive_learning_tables
Create Date: 2026-02-20

- alpha_features: candidate/validated/rejected features with formula and status
- alpha_experiments: A/B experiment runs with metrics
- alpha_strategy_nodes: predictive signals (nodes)
- alpha_strategy_edges: interaction strength between signals
- alpha_decay_log: deprecation/decay events
- alpha_meta_state: meta learning controller state
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "055_alpha_engine_tables"
down_revision = "054_institutional_adaptive_learning_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # alpha_features: feature_id, feature_name, feature_formula, status (TESTING/VALIDATED/REJECTED/DEPRECATED)
    op.create_table(
        "alpha_features",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("feature_name", sa.String(), nullable=False),
        sa.Column("feature_formula", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="TESTING"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deprecated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("weight_cap", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_alpha_features_status", "alpha_features", ["status"])
    op.create_index("idx_alpha_features_name", "alpha_features", ["feature_name"], unique=True)

    # alpha_experiments: experiment_id, feature_id, group_a/b metrics, promoted
    op.create_table(
        "alpha_experiments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("feature_id", sa.UUID(), nullable=True),
        sa.Column("experiment_name", sa.String(), nullable=False),
        sa.Column("group_a_accuracy", sa.Float(), nullable=True),
        sa.Column("group_b_accuracy", sa.Float(), nullable=True),
        sa.Column("group_a_brier_score", sa.Float(), nullable=True),
        sa.Column("group_b_brier_score", sa.Float(), nullable=True),
        sa.Column("group_a_clv", sa.Float(), nullable=True),
        sa.Column("group_b_clv", sa.Float(), nullable=True),
        sa.Column("group_a_roi", sa.Float(), nullable=True),
        sa.Column("group_b_roi", sa.Float(), nullable=True),
        sa.Column("sample_size_a", sa.Integer(), nullable=True),
        sa.Column("sample_size_b", sa.Integer(), nullable=True),
        sa.Column("p_value", sa.Float(), nullable=True),
        sa.Column("promoted", sa.Boolean(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("correlation_id", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_alpha_experiments_feature", "alpha_experiments", ["feature_id"])
    op.create_index("idx_alpha_experiments_started", "alpha_experiments", ["started_at"])

    # alpha_strategy_nodes: signal name, current weight, updated_at
    op.create_table(
        "alpha_strategy_nodes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("signal_name", sa.String(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_alpha_strategy_nodes_signal", "alpha_strategy_nodes", ["signal_name"], unique=True)

    # alpha_strategy_edges: from_node_id, to_node_id, interaction_strength
    op.create_table(
        "alpha_strategy_edges",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("from_node_id", sa.UUID(), nullable=False),
        sa.Column("to_node_id", sa.UUID(), nullable=False),
        sa.Column("interaction_strength", sa.Float(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_alpha_strategy_edges_from", "alpha_strategy_edges", ["from_node_id"])
    op.create_index("idx_alpha_strategy_edges_to", "alpha_strategy_edges", ["to_node_id"])

    # alpha_decay_log: feature_id, reason, ic_before, roi_before, created_at
    op.create_table(
        "alpha_decay_log",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("feature_id", sa.UUID(), nullable=True),
        sa.Column("feature_name", sa.String(), nullable=True),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("ic_before", sa.Float(), nullable=True),
        sa.Column("roi_before", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_alpha_decay_log_feature", "alpha_decay_log", ["feature_id"])

    # alpha_meta_state: learning_paused, last_retrain_at, last_experiment_at, regime
    op.create_table(
        "alpha_meta_state",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("learning_paused", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("last_retrain_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_experiment_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("regime", sa.String(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("alpha_meta_state")
    op.drop_index("idx_alpha_decay_log_feature", table_name="alpha_decay_log")
    op.drop_table("alpha_decay_log")
    op.drop_index("idx_alpha_strategy_edges_to", table_name="alpha_strategy_edges")
    op.drop_index("idx_alpha_strategy_edges_from", table_name="alpha_strategy_edges")
    op.drop_table("alpha_strategy_edges")
    op.drop_index("idx_alpha_strategy_nodes_signal", table_name="alpha_strategy_nodes")
    op.drop_table("alpha_strategy_nodes")
    op.drop_index("idx_alpha_experiments_started", table_name="alpha_experiments")
    op.drop_index("idx_alpha_experiments_feature", table_name="alpha_experiments")
    op.drop_table("alpha_experiments")
    op.drop_index("idx_alpha_features_name", table_name="alpha_features")
    op.drop_index("idx_alpha_features_status", table_name="alpha_features")
    op.drop_table("alpha_features")
