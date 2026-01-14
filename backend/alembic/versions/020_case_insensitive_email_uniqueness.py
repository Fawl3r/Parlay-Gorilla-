"""Enforce case-insensitive uniqueness for users.email (Postgres).

Revision ID: 020_case_insensitive_email_uniqueness
Revises: 019_add_ls_affiliate_mapping_and_commission_settlement
Create Date: 2025-12-27
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import context
from alembic import op


# revision identifiers, used by Alembic.
revision = "020_case_insensitive_email_uniqueness"
down_revision = "019_add_ls_affiliate_mapping_and_commission_settlement"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = getattr(bind, "dialect", None)
    if not dialect or dialect.name != "postgresql":
        # SQLite/dev uses GUID stored as string and cannot do a concurrent functional index.
        # App-layer normalization still protects auth behavior in dev.
        return

    # Fail fast if duplicates exist by lower(email) to avoid destructive behavior.
    # Offline SQL generation provides a mock bind that cannot return result sets.
    # Skip the duplicate check in offline mode so `alembic upgrade --sql` can render.
    if not context.is_offline_mode():
        dup = bind.execute(
            sa.text(
                """
                SELECT lower(email) AS email_norm, COUNT(*) AS cnt
                FROM users
                GROUP BY lower(email)
                HAVING COUNT(*) > 1
                LIMIT 1
                """
            )
        ).fetchone()
        if dup is not None:
            raise RuntimeError(
                "Cannot enforce case-insensitive email uniqueness; duplicates exist for lower(email). "
                "Run backend/scripts/check_case_insensitive_email_duplicates.py and fix duplicates first."
            )

    # Backfill: normalize stored emails.
    op.execute(sa.text("UPDATE users SET email = lower(email) WHERE email <> lower(email)"))

    # Create a unique functional index for case-insensitive uniqueness.
    #
    # Use CONCURRENTLY to reduce locking (must run outside a transaction).
    with op.get_context().autocommit_block():
        op.execute(sa.text("CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS ux_users_email_lower ON users (lower(email))"))


def downgrade() -> None:
    bind = op.get_bind()
    dialect = getattr(bind, "dialect", None)
    if not dialect or dialect.name != "postgresql":
        return

    with op.get_context().autocommit_block():
        op.execute(sa.text("DROP INDEX CONCURRENTLY IF EXISTS ux_users_email_lower"))


