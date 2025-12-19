"""
Credit balance service.

This module centralizes credit-balance reads/writes and provides an atomic
"spend if available" operation.

Credits are stored on `User.credit_balance` (integer).
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

logger = logging.getLogger(__name__)


class CreditBalanceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_balance(self, user_id: str) -> int:
        user_uuid = _parse_user_uuid(user_id)
        res = await self.db.execute(select(User.credit_balance).where(User.id == user_uuid))
        balance = res.scalar_one_or_none()
        return int(balance or 0)

    async def try_spend(self, user_id: str, credits: int) -> Optional[int]:
        """
        Atomically spend credits if the user has enough.

        Returns:
            New credit balance if spent successfully, else None.
        """
        if credits <= 0:
            logger.warning("try_spend called with non-positive credits=%s (user_id=%s)", credits, user_id)
            return await self.get_balance(user_id)

        user_uuid = _parse_user_uuid(user_id)

        # Atomic update: only spend if balance is sufficient.
        stmt = (
            update(User)
            .where(User.id == user_uuid)
            .where(User.credit_balance >= credits)
            .values(credit_balance=User.credit_balance - credits)
        )

        # Prefer RETURNING if available (Postgres, newer SQLite).
        try:
            stmt = stmt.returning(User.credit_balance)
            res = await self.db.execute(stmt)
            new_balance = res.scalar_one_or_none()
            if new_balance is None:
                await self.db.rollback()
                return None
            await self.db.commit()
            return int(new_balance)
        except Exception:
            # Fallback path for databases that don't support RETURNING.
            res = await self.db.execute(stmt)
            if getattr(res, "rowcount", 0) != 1:
                await self.db.rollback()
                return None
            await self.db.commit()
            return await self.get_balance(user_id)


def _parse_user_uuid(user_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(user_id))
    except Exception as exc:
        raise ValueError(f"Invalid user_id: {user_id}") from exc


