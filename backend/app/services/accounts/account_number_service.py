"""Account number generation and allocation.

Requirements:
- Every User must have a stable, non-PII `account_number`.
- It must be unique.
- It should be safe to include in on-chain inscriptions.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


@dataclass(frozen=True)
class AccountNumberConfig:
    digits: int = 10
    max_attempts: int = 25


class AccountNumberGenerator:
    """Generates user-facing numeric account numbers."""

    def __init__(self, *, config: AccountNumberConfig | None = None):
        self._config = config or AccountNumberConfig()

    def generate_candidate(self) -> str:
        n = secrets.randbelow(10 ** self._config.digits)
        return str(n).zfill(self._config.digits)


class AccountNumberAllocator:
    """Allocates a unique account number against the database."""

    def __init__(self, *, generator: AccountNumberGenerator | None = None, config: AccountNumberConfig | None = None):
        self._config = config or AccountNumberConfig()
        self._generator = generator or AccountNumberGenerator(config=self._config)

    async def allocate(self, db: AsyncSession) -> str:
        for _ in range(self._config.max_attempts):
            candidate = self._generator.generate_candidate()
            res = await db.execute(select(User.id).where(User.account_number == candidate))
            if res.scalar_one_or_none() is None:
                return candidate
        raise RuntimeError("Failed to allocate a unique account number")


