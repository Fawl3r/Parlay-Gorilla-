"""Add fetch budget tracking table.

Revision ID: 031_add_fetch_budget_tracking
Revises: 030_add_gorilla_bot_kb
Create Date: 2026-01-XX
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "031_add_fetch_budget_tracking"
down_revision = "030_add_gorilla_bot_kb"
branch_labels = None
depends_on = None


def _is_postgres() -> bool:
    bind = op.get_bind()
    return bind is not None and bind.dialect.name == "postgresql"


def upgrade() -> None:
    op.create_table(
        "fetch_budget_tracking",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("fetch_key", sa.String, unique=True, nullable=False),
        sa.Column("last_fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ttl_seconds", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_fetch_budget_tracking_fetch_key", "fetch_budget_tracking", ["fetch_key"])
    op.create_index("ix_fetch_budget_tracking_last_fetched", "fetch_budget_tracking", ["last_fetched_at"])


def downgrade() -> None:
    op.drop_index("ix_fetch_budget_tracking_last_fetched", table_name="fetch_budget_tracking")
    op.drop_index("ix_fetch_budget_tracking_fetch_key", table_name="fetch_budget_tracking")
    op.drop_table("fetch_budget_tracking")
