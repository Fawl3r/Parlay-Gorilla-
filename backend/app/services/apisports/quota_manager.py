"""
API-Sports daily quota per sport: 75/day per sport (America/Chicago).
Yellow at 60 (non-critical blocked); red at 75 (all blocked).
Uses Redis when available; falls back to DB table api_quota_usage (date, sport).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.core.config import settings
from app.core.event_logger import log_event
from app.services.redis.redis_client_provider import get_redis_provider

logger = logging.getLogger(__name__)

CHICAGO = ZoneInfo("America/Chicago")
QUOTA_KEY_PREFIX = "apisports:quota:"
CIRCUIT_BREAKER_KEY = "apisports:circuit_breaker:open_until"
DAILY_LIMIT = 75
YELLOW_THRESHOLD = 60
RED_THRESHOLD = 75


def _today_chicago() -> str:
    return datetime.now(CHICAGO).strftime("%Y-%m-%d")


@dataclass
class QuotaDecision:
    """Result of a quota check: allowed, reason, used, limit, sport."""
    allowed: bool
    reason: str
    used: int
    limit: int
    sport: str


class QuotaManager:
    """
    Enforces daily request budget per sport (75/day).
    - can_spend(sport, n, critical=False) -> bool
    - spend(sport, n) -> None
    - remaining_async(sport) -> int
    Yellow (60): non-critical blocked; red (75): all blocked.
    """

    def __init__(
        self,
        *,
        daily_limit: int | None = None,
        circuit_failures: int | None = None,
        circuit_cooldown_seconds: int | None = None,
    ):
        self._daily_limit = daily_limit or getattr(settings, "apisports_daily_quota", DAILY_LIMIT)
        self._circuit_failures = circuit_failures or getattr(
            settings, "apisports_circuit_breaker_failures", 5
        )
        self._circuit_cooldown = circuit_cooldown_seconds or getattr(
            settings, "apisports_circuit_breaker_cooldown_seconds", 1800
        )
        self._failure_count = 0
        self._redis = get_redis_provider()

    def _quota_key(self, sport: str) -> str:
        sport_key = (sport or "default").lower().strip()
        return f"{QUOTA_KEY_PREFIX}{sport_key}:{_today_chicago()}"

    def _use_redis(self) -> bool:
        return self._redis.is_configured()

    async def _get_used_redis(self, sport: str) -> int:
        try:
            client = self._redis.get_client()
            key = self._quota_key(sport)
            raw = await client.get(key)
            if raw is None:
                return 0
            return int(raw.decode("utf-8"))
        except Exception as e:
            logger.warning("QuotaManager Redis get failed: %s", e)
            return 0

    async def _incr_redis(self, sport: str, n: int) -> None:
        try:
            client = self._redis.get_client()
            key = self._quota_key(sport)
            await client.incrby(key, n)
            await client.expire(key, 86400 * 2)
        except Exception as e:
            logger.warning("QuotaManager Redis incr failed: %s", e)
            raise

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

    async def check_quota(
        self,
        sport: str,
        n: int = 1,
        critical: bool = False,
    ) -> QuotaDecision:
        """
        Return decision: allowed, reason, used, limit.
        Non-critical blocked when used >= yellow (60); all blocked when used >= red (75).
        """
        sport_key = (sport or "default").lower().strip()
        if self._use_redis():
            try:
                open_until = await self._get_circuit_open_until_redis()
                if open_until is not None and open_until > datetime.now().timestamp():
                    log_event(
                        logger,
                        "provider.quota.state",
                        sport=sport_key,
                        allowed=False,
                        reason="circuit_breaker_open",
                    )
                    return QuotaDecision(
                        allowed=False,
                        reason="circuit_breaker_open",
                        used=0,
                        limit=self._daily_limit,
                        sport=sport_key,
                    )
                used = await self._get_used_redis(sport_key)
            except Exception as e:
                logger.warning("QuotaManager Redis check failed, falling back to DB: %s", e)
                used = await self._get_used_db(sport_key)
        else:
            used = await self._get_used_db(sport_key)
        if used >= RED_THRESHOLD:
            log_event(
                logger,
                "provider.quota.state",
                sport=sport_key,
                allowed=False,
                reason="red_limit",
                used=used,
                limit=self._daily_limit,
            )
            return QuotaDecision(
                allowed=False,
                reason="red_limit",
                used=used,
                limit=self._daily_limit,
                sport=sport_key,
            )
        if not critical and used >= YELLOW_THRESHOLD:
            log_event(
                logger,
                "provider.quota.state",
                sport=sport_key,
                allowed=False,
                reason="yellow_limit",
                used=used,
                limit=self._daily_limit,
            )
            return QuotaDecision(
                allowed=False,
                reason="yellow_limit",
                used=used,
                limit=self._daily_limit,
                sport=sport_key,
            )
        if used + n > self._daily_limit:
            return QuotaDecision(
                allowed=False,
                reason="over_limit",
                used=used,
                limit=self._daily_limit,
                sport=sport_key,
            )
        return QuotaDecision(
            allowed=True,
            reason="ok",
            used=used,
            limit=self._daily_limit,
            sport=sport_key,
        )

    async def _get_used_db(self, sport: str) -> int:
        try:
            from app.database.session import AsyncSessionLocal
            from app.models.api_quota_usage import ApiQuotaUsage
            today = _today_chicago()
            sport_key = (sport or "default").lower().strip()
            async with AsyncSessionLocal() as db:
                row = await db.execute(
                    select(ApiQuotaUsage).where(
                        ApiQuotaUsage.date == today,
                        ApiQuotaUsage.sport == sport_key,
                    )
                )
                r = row.scalar_one_or_none()
                return r.used if r else 0
        except Exception as e:
            logger.warning("QuotaManager DB get failed: %s", e)
            return 0

    async def can_spend(
        self,
        sport: str,
        n: int = 1,
        critical: bool = False,
    ) -> bool:
        """Return True if we can spend n calls for this sport without exceeding daily limit."""
        decision = await self.check_quota(sport, n=n, critical=critical)
        return decision.allowed

    async def spend(self, sport: str, n: int = 1) -> None:
        """Record n requests as used for this sport."""
        sport_key = (sport or "default").lower().strip()
        if self._use_redis():
            try:
                await self._incr_redis(sport_key, n)
                log_event(
                    logger,
                    "provider.quota.spend",
                    sport=sport_key,
                    n=n,
                )
                return
            except Exception as e:
                logger.warning("QuotaManager Redis spend failed, falling back to DB: %s", e)
        from app.database.session import AsyncSessionLocal
        from app.models.api_quota_usage import ApiQuotaUsage
        try:
            async with AsyncSessionLocal() as db:
                today = _today_chicago()
                row = await db.execute(
                    select(ApiQuotaUsage).where(
                        ApiQuotaUsage.date == today,
                        ApiQuotaUsage.sport == sport_key,
                    )
                )
                r = row.scalar_one_or_none()
                if r:
                    r.used += n
                    r.updated_at = datetime.now(timezone.utc)
                else:
                    db.add(ApiQuotaUsage(date=today, sport=sport_key, used=n))
                await db.commit()
            log_event(logger, "provider.quota.spend", sport=sport_key, n=n)
        except Exception as e:
            logger.warning("QuotaManager DB spend failed: %s", e)

    async def remaining_async(self, sport: str = "default") -> int:
        """Return remaining calls for today for this sport."""
        sk = (sport or "default").lower().strip()
        used = await self._get_used_redis(sk) if self._use_redis() else await self._get_used_db(sk)
        return max(0, self._daily_limit - used)

    async def used_today_async(self, sport: str = "default") -> int:
        """Return number of calls used today for this sport."""
        sk = (sport or "default").lower().strip()
        if self._use_redis():
            try:
                return await self._get_used_redis(sk)
            except Exception:
                pass
        return await self._get_used_db(sk)

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
        self._failure_count = 0

    async def is_circuit_open(self) -> bool:
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
