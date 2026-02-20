"""Add idempotency_key to model_predictions for duplicate prevention.

Revision ID: 058_idempotency_key
Revises: 057_alpha_meta_state_status
Create Date: 2026-02-20

- idempotency_key: sha256(sport|event_id|market_type|selection|model_version|day_bucket)
- Unique index so same key cannot be inserted twice (retries/analysis reruns).
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "058_idempotency_key"
down_revision = "057_alpha_meta_state_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "model_predictions",
        sa.Column("idempotency_key", sa.String(64), nullable=True),
    )
    op.create_index(
        "idx_model_predictions_idempotency_key",
        "model_predictions",
        ["idempotency_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("idx_model_predictions_idempotency_key", table_name="model_predictions")
    op.drop_column("model_predictions", "idempotency_key")
