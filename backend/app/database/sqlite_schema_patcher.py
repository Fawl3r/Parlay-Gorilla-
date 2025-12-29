"""SQLite dev schema patcher.

Why this exists:
- In local dev we often run with USE_SQLITE=true.
- We rely on `Base.metadata.create_all()` at startup (not Alembic) for convenience.
- `create_all()` will NOT add columns to existing tables, so older dev DB files can
  drift and cause runtime `sqlite3.OperationalError: no such column ...` crashes.

This patcher performs safe, additive schema updates (ADD COLUMN only) so the API
can start and handle requests reliably without forcing devs to delete their DB.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Mapping, Optional, Set

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SqliteRequiredColumnsSpec:
    """A list of required columns for an existing SQLite table."""

    table_name: str
    required_columns: Mapping[str, str]


class SqliteSchemaPatcher:
    """Additive (ADD COLUMN) schema patcher for SQLite dev databases."""

    def __init__(self, conn: AsyncConnection):
        self._conn = conn

    async def ensure_dev_schema(self) -> None:
        """Ensure known-migrated columns exist for common tables in dev SQLite."""
        for spec in SQLITE_DEV_REQUIRED_COLUMNS:
            await self._ensure_table_columns(spec)

    async def _ensure_table_columns(self, spec: SqliteRequiredColumnsSpec) -> None:
        if not await self._table_exists(spec.table_name):
            return

        existing = await self._get_existing_columns(spec.table_name)
        added: list[str] = []

        for column_name, column_def in spec.required_columns.items():
            if column_name in existing:
                continue
            try:
                await self._conn.execute(
                    text(f"ALTER TABLE {spec.table_name} ADD COLUMN {column_name} {column_def}")
                )
                added.append(column_name)
                await self._backfill_default_if_present(spec.table_name, column_name, column_def)
            except Exception as e:
                # Best-effort: ignore duplicate-column races; log everything else.
                if "duplicate column" in str(e).lower():
                    continue
                logger.warning(
                    "SQLite schema patch failed adding %s.%s: %s",
                    spec.table_name,
                    column_name,
                    e,
                )

        if added:
            logger.info(
                "SQLite schema patch: added %d column(s) to %s: %s",
                len(added),
                spec.table_name,
                ", ".join(added),
            )

    async def _table_exists(self, table_name: str) -> bool:
        result = await self._conn.execute(
            text(
                """
                SELECT 1
                FROM sqlite_master
                WHERE type='table' AND name=:table_name
                LIMIT 1
                """
            ),
            {"table_name": table_name},
        )
        return result.scalar() is not None

    async def _get_existing_columns(self, table_name: str) -> Set[str]:
        result = await self._conn.execute(text(f"PRAGMA table_info({table_name})"))
        return {row[1] for row in result}

    async def _backfill_default_if_present(self, table: str, column: str, column_def: str) -> None:
        default_expr = self._extract_default_expr(column_def)
        if not default_expr:
            return
        try:
            await self._conn.execute(
                text(f"UPDATE {table} SET {column} = {default_expr} WHERE {column} IS NULL")
            )
        except Exception as e:
            logger.warning("SQLite default backfill failed for %s.%s: %s", table, column, e)

    def _extract_default_expr(self, column_def: str) -> Optional[str]:
        # Column defs in this module are controlled constants, so a simple parse is OK.
        upper = column_def.upper()
        if "DEFAULT" not in upper:
            return None
        # Keep the original casing/quoting of the default expression.
        parts = column_def.split("DEFAULT", 1)
        if len(parts) != 2:
            return None
        default_expr = parts[1].strip()
        return default_expr or None


# --------------------------------------------------------------------------------------
# Known columns that older dev SQLite DBs may be missing.
# These mirror Alembic migrations that we rely on in Postgres, but patch in-place for
# SQLite dev convenience.
# --------------------------------------------------------------------------------------

SQLITE_USERS_REQUIRED_COLUMNS: Mapping[str, str] = {
    # Migration 002
    "role": "VARCHAR NOT NULL DEFAULT 'user'",
    "plan": "VARCHAR NOT NULL DEFAULT 'free'",
    "is_active": "BOOLEAN NOT NULL DEFAULT 1",
    # Migration 004
    "email_verified": "BOOLEAN NOT NULL DEFAULT 0",
    "profile_completed": "BOOLEAN NOT NULL DEFAULT 0",
    "bio": "TEXT",
    "timezone": "VARCHAR(50)",
    # Migration 008
    "password_hash": "VARCHAR",
    "free_parlays_total": "INTEGER NOT NULL DEFAULT 2",
    "free_parlays_used": "INTEGER NOT NULL DEFAULT 0",
    "subscription_plan": "VARCHAR(50)",
    "subscription_status": "VARCHAR(20) NOT NULL DEFAULT 'none'",
    "subscription_renewal_date": "TIMESTAMP",
    "subscription_last_billed_at": "TIMESTAMP",
    "daily_parlays_used": "INTEGER NOT NULL DEFAULT 0",
    "daily_parlays_usage_date": "DATE",
    "credit_balance": "INTEGER NOT NULL DEFAULT 0",
    "affiliate_id": "VARCHAR(36)",
    "referred_by_affiliate_id": "VARCHAR(36)",
    # Migration 012 (this is the current crash source on old dev DBs)
    "premium_ai_parlays_used": "INTEGER NOT NULL DEFAULT 0",
    "premium_ai_parlays_period_start": "TIMESTAMP",
    # Migration 022 (premium rolling-period quotas)
    "premium_custom_builder_used": "INTEGER NOT NULL DEFAULT 0",
    "premium_custom_builder_period_start": "TIMESTAMP",
    "premium_inscriptions_used": "INTEGER NOT NULL DEFAULT 0",
    "premium_inscriptions_period_start": "TIMESTAMP",
    # Migration 013
    "account_number": "VARCHAR(20)",
}

SQLITE_AFFILIATES_REQUIRED_COLUMNS: Mapping[str, str] = {
    # Migration 009
    "tax_form_type": "VARCHAR(20)",
    "tax_form_status": "VARCHAR(20) NOT NULL DEFAULT 'not_submitted'",
    "tax_form_submitted_at": "TIMESTAMP",
    "tax_form_verified_at": "TIMESTAMP",
    "legal_name": "VARCHAR(255)",
    "business_name": "VARCHAR(255)",
    "tax_classification": "VARCHAR(50)",
    "tax_address_street": "VARCHAR(255)",
    "tax_address_city": "VARCHAR(100)",
    "tax_address_state": "VARCHAR(50)",
    "tax_address_zip": "VARCHAR(20)",
    "tax_address_country": "VARCHAR(100) DEFAULT 'US'",
    "tax_id_number": "VARCHAR(50)",
    "tax_id_type": "VARCHAR(20)",
    "country_of_residence": "VARCHAR(100)",
    "foreign_tax_id": "VARCHAR(50)",
    "tax_form_signed_at": "TIMESTAMP",
    "tax_form_ip_address": "VARCHAR(45)",
    "tax_form_required_threshold": "NUMERIC(10, 2) NOT NULL DEFAULT 600.00",
    # Migration 019
    "lemonsqueezy_affiliate_code": "VARCHAR(50)",
}

SQLITE_AFFILIATE_COMMISSIONS_REQUIRED_COLUMNS: Mapping[str, str] = {
    # Migration 019
    "settlement_provider": "VARCHAR(20) NOT NULL DEFAULT 'internal'",
}

SQLITE_SAVED_PARLAYS_REQUIRED_COLUMNS: Mapping[str, str] = {
    # Migration 023
    "inscription_quota_consumed": "BOOLEAN NOT NULL DEFAULT 0",
}

SQLITE_DEV_REQUIRED_COLUMNS = [
    SqliteRequiredColumnsSpec("users", SQLITE_USERS_REQUIRED_COLUMNS),
    SqliteRequiredColumnsSpec("affiliates", SQLITE_AFFILIATES_REQUIRED_COLUMNS),
    SqliteRequiredColumnsSpec("affiliate_commissions", SQLITE_AFFILIATE_COMMISSIONS_REQUIRED_COLUMNS),
    SqliteRequiredColumnsSpec("saved_parlays", SQLITE_SAVED_PARLAYS_REQUIRED_COLUMNS),
]


