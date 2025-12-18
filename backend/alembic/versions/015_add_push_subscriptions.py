"""Add push_subscriptions table for Web Push notifications.

Revision ID: 015_add_push_subscriptions
Revises: 014_add_credit_pack_purchases
Create Date: 2025-12-18
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "015_add_push_subscriptions"
down_revision = "014_add_credit_pack_purchases"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "push_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("endpoint", sa.Text(), nullable=False),
        sa.Column("p256dh", sa.String(length=255), nullable=False),
        sa.Column("auth", sa.String(length=255), nullable=False),
        sa.Column("expiration_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("endpoint", name="uq_push_subscriptions_endpoint"),
    )

    op.create_index("ix_push_subscriptions_created_at", "push_subscriptions", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_push_subscriptions_created_at", table_name="push_subscriptions")
    op.drop_table("push_subscriptions")


