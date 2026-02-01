"""Add missing user metadata/profile columns if absent (idempotent).

Brings users table in sync with User model: created_at, updated_at,
display_name, avatar_url, last_login. Safe to run when columns already exist.

Revision ID: 046_add_user_metadata_columns
Revises: 045_add_apisports_team_and_rosters
Create Date: 2026-01-31

"""

from __future__ import annotations

from sqlalchemy import inspect
from alembic import op
import sqlalchemy as sa

revision = "046_add_user_metadata_columns"
down_revision = "045_add_apisports_team_and_rosters"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    if "users" not in inspector.get_table_names():
        return

    existing = {col["name"] for col in inspector.get_columns("users")}

    if "created_at" not in existing:
        op.add_column(
            "users",
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=True,
            ),
        )

    if "updated_at" not in existing:
        op.add_column(
            "users",
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=True,
            ),
        )

    if "display_name" not in existing:
        op.add_column(
            "users",
            sa.Column("display_name", sa.String(), nullable=True),
        )

    if "avatar_url" not in existing:
        op.add_column(
            "users",
            sa.Column("avatar_url", sa.String(), nullable=True),
        )

    if "last_login" not in existing:
        op.add_column(
            "users",
            sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        )


def downgrade() -> None:
    # Irreversible: we do not drop columns that may hold data.
    pass
