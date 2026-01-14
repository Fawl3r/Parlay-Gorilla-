"""Add users.account_number for on-chain inscriptions (non-PII).

Revision ID: 013_add_user_account_number
Revises: 012_add_premium_ai_parlays_monthly
Create Date: 2025-12-18
"""

from __future__ import annotations

import secrets

from alembic import context
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = "013_add_user_account_number"
down_revision = "012_add_premium_ai_parlays_monthly"
branch_labels = None
depends_on = None


_ACCOUNT_NUMBER_DIGITS = 10


def _generate_account_number() -> str:
    n = secrets.randbelow(10 ** _ACCOUNT_NUMBER_DIGITS)
    return str(n).zfill(_ACCOUNT_NUMBER_DIGITS)


def upgrade() -> None:
    # Add nullable first, backfill, then enforce NOT NULL + UNIQUE.
    op.add_column("users", sa.Column("account_number", sa.String(length=20), nullable=True))

    conn = op.get_bind()

    # Offline SQL generation has no DB connection; skip the Python-level backfill.
    # This does NOT affect real migrations (online mode), which still backfill
    # before enforcing NOT NULL + UNIQUE.
    if conn is not None and not context.is_offline_mode():
        existing_rows = conn.execute(
            text("SELECT account_number FROM users WHERE account_number IS NOT NULL AND account_number <> ''")
        ).fetchall()
        existing = {str(r[0]) for r in existing_rows if r and r[0]}

        missing_rows = conn.execute(
            text("SELECT id FROM users WHERE account_number IS NULL OR account_number = ''")
        ).fetchall()

        for (user_id,) in missing_rows:
            while True:
                candidate = _generate_account_number()
                if candidate in existing:
                    continue
                already = conn.execute(
                    text("SELECT 1 FROM users WHERE account_number = :candidate LIMIT 1"),
                    {"candidate": candidate},
                ).first()
                if already:
                    continue
                conn.execute(
                    text("UPDATE users SET account_number = :candidate WHERE id = :user_id"),
                    {"candidate": candidate, "user_id": user_id},
                )
                existing.add(candidate)
                break

    op.alter_column("users", "account_number", nullable=False)
    op.create_index("ix_users_account_number", "users", ["account_number"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_account_number", table_name="users")
    op.drop_column("users", "account_number")


