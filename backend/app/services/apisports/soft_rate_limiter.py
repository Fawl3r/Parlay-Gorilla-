"""
API-Sports soft rate limiter: token bucket to avoid bursts.

Config: 1 request per 10–20 seconds during refresh, burst <= 2.
Uses Redis when available; fallback is in-process lock + sleep (refresh workers only).
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional

from app.core.config import settings
from app.services.redis.redis_client_provider import get_redis_provider

logger = logging.getLogger(__name__)

BUCKET_KEY = "apisports:bucket:tokens"
BUCKET_LAST_REFILL_KEY = "apisports:bucket:last_refill"


class SoftRateLimiter:
    """
    Token bucket: refill every interval_seconds, max burst tokens.
    acquire() blocks until a token is available or timeout.
    """

    def __init__(
        self,
        *,
        interval_seconds: Optional[int] = None,
        burst: Optional[int] = None,
    ):
        self._interval = interval_seconds or getattr(
            settings, "apisports_soft_rps_interval_seconds", 15
        )
        self._burst = burst or getattr(settings, "apisports_burst", 2)
        self._redis = get_redis_provider()
        self._local_tokens = float(self._burst)
        self._local_last_refill = time.monotonic()
        self._local_lock = asyncio.Lock()

    def _use_redis(self) -> bool:
        return self._redis.is_configured()

    async def _acquire_redis(self, timeout_seconds: float = 30.0) -> bool:
        """Try to consume one token from Redis bucket. Refill over time. Returns True if acquired."""
        try:
            client = self._redis.get_client()
            now = time.time()
            # Lua: get last_refill, compute new tokens, if tokens >= 1 then decrement and set last_refill, return 1 else 0
            script = """
            local last = tonumber(redis.call("GET", KEYS[2]) or "0")
            local interval = tonumber(ARGV[1])
            local burst = tonumber(ARGV[2])
            local now = tonumber(ARGV[3])
            local elapsed = math.max(0, now - last)
            local refill = math.floor(elapsed / interval)
            local tokens_key = KEYS[1]
            local current = tonumber(redis.call("GET", tokens_key) or burst)
            current = math.min(burst, current + refill)
            if current >= 1 then
                redis.call("SET", tokens_key, current - 1)
                redis.call("SET", KEYS[2], now)
                return 1
            end
            return 0
            """
            keys = [BUCKET_KEY, BUCKET_LAST_REFILL_KEY]
            args = [str(self._interval), str(self._burst), str(now)]
            result = await client.eval(script, 2, *keys, *args)
            if result == 1:
                return True
            return False
        except Exception as e:
            logger.warning("SoftRateLimiter Redis acquire failed: %s", e)
            return False

    async def acquire(self, timeout_seconds: float = 30.0) -> bool:
        """
        Acquire one token. If Redis: try once (non-blocking). If in-process fallback: sleep until token available or timeout.
        Returns True if token acquired, False if timeout or Redis unavailable.
        """
        if self._use_redis():
            result = await self._acquire_redis(timeout_seconds)
            # If Redis fails, fall back to local mode
            if result:
                return True
            # Redis failed or no token available - fall through to local fallback
            logger.info("SoftRateLimiter: Redis unavailable or no token, using local fallback")
        
        async with self._local_lock:
            now = time.monotonic()
            elapsed = now - self._local_last_refill
            refill = int(elapsed / self._interval)
            if refill > 0:
                self._local_tokens = min(self._burst, self._local_tokens + refill)
                self._local_last_refill = now
            if self._local_tokens >= 1:
                self._local_tokens -= 1
                return True
            wait_for = self._interval - (elapsed % self._interval)
            if wait_for > timeout_seconds:
                return False
            await asyncio.sleep(min(wait_for, timeout_seconds))
            self._local_last_refill = time.monotonic()
            self._local_tokens = min(self._burst, self._local_tokens) - 1
            if self._local_tokens < 0:
                self._local_tokens = 0
            return True
        return False


_soft_rate_limiter: Optional[SoftRateLimiter] = None


def get_soft_rate_limiter() -> SoftRateLimiter:
    global _soft_rate_limiter
    if _soft_rate_limiter is None:
        _soft_rate_limiter = SoftRateLimiter()
    return _soft_rate_limiter
