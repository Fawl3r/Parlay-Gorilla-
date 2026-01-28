"""
API-Sports daily quota manager: hard cap 100/day (America/Chicago).

Uses Redis when available; falls back to DB table api_quota_usage.
Circuit breaker: after N consecutive failures, pause API usage for cooldown seconds.
"""

from __future__ import annotations

import logging
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

from app.core.config import settings
from app.services.redis.redis_client_provider import get_redis_provider

logger = logging.getLogger(__name__)

CHICAGO = ZoneInfo("America/Chicago")
QUOTA_KEY_PREFIX = "apisports:quota:"
CIRCUIT_BREAKER_KEY = "apisports:circuit_breaker:open_until"


def _today_chicago() -> str:
    """Return today's date in America/Chicago as YYYY-MM-DD."""
    return datetime.now(CHICAGO).strftime("%Y-%m-%d")


class QuotaManager:
    """
    Enforces daily request budget for API-Sports.
    - can_spend(n) -> bool
    - spend(n) -> None
    - remaining() -> int
    - reset_if_new_day() -> None (called internally when date changes)
    """

    def __init__(
        self,
        *,
        daily_limit: int | None = None,
        circuit_failures: int | None = None,
        circuit_cooldown_seconds: int | None = None,
    ):
        self._daily_limit = daily_limit or getattr(settings, "apisports_daily_quota", 100)
        self._circuit_failures = circuit_failures or getattr(
            settings, "apisports_circuit_breaker_failures", 5
        )
        self._circuit_cooldown = circuit_cooldown_seconds or getattr(
            settings, "apisports_circuit_breaker_cooldown_seconds", 1800
        )
        self._failure_count = 0
        self._redis = get_redis_provider()

    def _quota_key(self) -> str:
        return f"{QUOTA_KEY_PREFIX}{_today_chicago()}"

    def _use_redis(self) -> bool:
        return self._redis.is_configured()

    async def _get_used_redis(self) -> int:
        try:
            client = self._redis.get_client()
            key = self._quota_key()
            raw = await client.get(key)
            if raw is None:
                return 0
            return int(raw.decode("utf-8"))
        except Exception as e:
            logger.warning("QuotaManager Redis get failed: %s", e)
            return 0

    async def _incr_redis(self, n: int) -> None:
        try:
            client = self._redis.get_client()
            key = self._quota_key()
            await client.incrby(key, n)
            await client.expire(key, 86400 * 2)
        except Exception as e:
            logger.warning("QuotaManager Redis incr failed: %s", e)
            raise  # Re-raise so spend() can catch and fall back to DB

    async def _get_circuit_open_until_redis(self) -> float | None:
        try:
            client = self._redis.get_client()
            raw = await client.get(CIRCUIT_BREAKER_KEY)
            if raw is None:
                return None
            return float(raw.decode("utf-8"))
        except Exception as e:
            logger.warning("QuotaManager circuit breaker get failed: %s", e)
            return None

    async def _set_circuit_open_redis(self, until_ts: float) -> None:
        try:
            client = self._redis.get_client()
            await client.set(
                CIRCUIT_BREAKER_KEY,
                str(until_ts),
                ex=int(self._circuit_cooldown + 60),
            )
        except Exception as e:
            logger.warning("QuotaManager circuit breaker set failed: %s", e)

    async def can_spend(self, n: int = 1) -> bool:
        """Return True if we can spend n calls without exceeding daily limit."""
        if self._use_redis():
            try:
                open_until = await self._get_circuit_open_until_redis()
                if open_until is not None and open_until > datetime.now().timestamp():
                    logger.info(
                        "QuotaManager: circuit breaker open until %s",
                        datetime.fromtimestamp(open_until).isoformat(),
                    )
                    return False
                used = await self._get_used_redis()
                return used + n <= self._daily_limit
            except Exception as e:
                logger.warning("QuotaManager Redis can_spend failed, falling back to DB: %s", e)
                # Fall through to DB fallback
        
        try:
            from app.database.session import AsyncSessionLocal
            from app.models.api_quota_usage import ApiQuotaUsage

            async with AsyncSessionLocal() as db:
                row = await db.get(ApiQuotaUsage, _today_chicago())
                used = row.used if row else 0
            return used + n <= self._daily_limit
        except Exception as e:
            logger.warning("QuotaManager DB can_spend failed: %s", e)
            return False

    async def spend(self, n: int = 1) -> None:
        """Record n requests as used."""
        if self._use_redis():
            try:
                await self._incr_redis(n)
                return
            except Exception as e:
                logger.warning("QuotaManager Redis spend failed, falling back to DB: %s", e)
                # Fall through to DB fallback
        
        from datetime import timezone
        from app.database.session import AsyncSessionLocal
        from app.models.api_quota_usage import ApiQuotaUsage

        try:
            async with AsyncSessionLocal() as db:
                today = _today_chicago()
                row = await db.get(ApiQuotaUsage, today)
                if row:
                    row.used += n
                    row.updated_at = datetime.now(timezone.utc)
                else:
                    row = ApiQuotaUsage(date=today, used=n)
                    db.add(row)
                await db.commit()
        except Exception as e:
            logger.warning("QuotaManager DB spend failed: %s", e)

    def remaining(self) -> int:
        """Synchronous remaining (for reporting). For accurate value use remaining_async()."""
        return self._daily_limit

    async def remaining_async(self) -> int:
        """Return remaining calls for today."""
        if self._use_redis():
            try:
                used = await self._get_used_redis()
                return max(0, self._daily_limit - used)
            except Exception as e:
                logger.warning("QuotaManager Redis remaining_async failed, falling back to DB: %s", e)
                # Fall through to DB fallback
        
        try:
            from app.database.session import AsyncSessionLocal
            from app.models.api_quota_usage import ApiQuotaUsage

            async with AsyncSessionLocal() as db:
                row = await db.get(ApiQuotaUsage, _today_chicago())
                used = row.used if row else 0
            return max(0, self._daily_limit - used)
        except Exception as e:
            logger.warning("QuotaManager DB remaining_async failed: %s", e)
            return self._daily_limit  # Safe default: assume full quota available

    async def used_today_async(self) -> int:
        """Return number of calls used today."""
        if self._use_redis():
            try:
                return await self._get_used_redis()
            except Exception as e:
                logger.warning("QuotaManager Redis used_today_async failed, falling back to DB: %s", e)
                # Fall through to DB fallback
        
        try:
            from app.database.session import AsyncSessionLocal
            from app.models.api_quota_usage import ApiQuotaUsage

            async with AsyncSessionLocal() as db:
                row = await db.get(ApiQuotaUsage, _today_chicago())
                return row.used if row else 0
        except Exception as e:
            logger.warning("QuotaManager DB used_today_async failed: %s", e)
            return 0  # Safe default

    async def reset_if_new_day(self) -> None:
        """No-op when using Redis (key is date-based). For DB, new row per day."""
        pass

    async def record_failure(self) -> None:
        """Record an API failure; open circuit breaker after threshold."""
        self._failure_count += 1
        if self._failure_count >= self._circuit_failures:
            until = datetime.now().timestamp() + self._circuit_cooldown
            if self._use_redis():
                await self._set_circuit_open_redis(until)
            logger.warning(
                "QuotaManager: circuit breaker opened for %s seconds after %s failures",
                self._circuit_cooldown,
                self._failure_count,
            )
            self._failure_count = 0

    async def record_success(self) -> None:
        """Reset failure count on success."""
        self._failure_count = 0

    async def is_circuit_open(self) -> bool:
        """Return True if circuit breaker is open."""
        if self._use_redis():
            open_until = await self._get_circuit_open_until_redis()
            return open_until is not None and open_until > datetime.now().timestamp()
        return False


_quota_manager: QuotaManager | None = None


def get_quota_manager() -> QuotaManager:
    global _quota_manager
    if _quota_manager is None:
        _quota_manager = QuotaManager()
    return _quota_manager
