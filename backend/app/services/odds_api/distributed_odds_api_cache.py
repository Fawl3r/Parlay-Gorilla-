from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Optional

from app.core.config import settings
from app.services.redis.redis_client_provider import RedisClientProvider, get_redis_provider
from app.services.redis.redis_distributed_lock import RedisDistributedLock

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DistributedOddsApiCacheConfig:
    cache_ttl_seconds: int = 172800  # 48 hours
    lock_ttl_seconds: int = 60
    wait_timeout_seconds: float = 15.0
    poll_interval_seconds: float = 0.25


class DistributedOddsApiCache:
    """
    Cluster-wide cache for Odds API responses (Redis-backed).

    Goals:
    - Ensure at most 1 external call per cache key per TTL across all instances.
    - Deduplicate concurrent in-flight calls via a distributed lock.
    - Fail open: callers can fall back to in-process caching if Redis is down.
    """

    KEY_PREFIX = "odds_api:v1:current_odds:"
    LOCK_PREFIX = "odds_api:v1:lock:"

    def __init__(
        self,
        *,
        provider: Optional[RedisClientProvider] = None,
        config: Optional[DistributedOddsApiCacheConfig] = None,
    ):
        self._provider = provider or get_redis_provider()
        ttl_seconds = int(getattr(settings, "odds_api_cache_ttl_seconds", 172800) or 172800)
        self._config = config or DistributedOddsApiCacheConfig(cache_ttl_seconds=ttl_seconds)

    def is_available(self) -> bool:
        return self._provider.is_configured()

    @staticmethod
    def build_cache_key(*, sport_key: str, regions: str, markets: str, odds_format: str) -> str:
        safe = lambda s: (str(s or "").strip() or "none")
        return f"{safe(sport_key)}|{safe(regions)}|{safe(markets)}|{safe(odds_format)}"

    def _redis_key(self, cache_key: str) -> str:
        return f"{self.KEY_PREFIX}{cache_key}"

    def _lock_key(self, cache_key: str) -> str:
        return f"{self.LOCK_PREFIX}{cache_key}"

    async def get(self, *, cache_key: str) -> Optional[Any]:
        client = self._provider.get_client()
        raw = await client.get(self._redis_key(cache_key))
        if not raw:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return None

    async def set(self, *, cache_key: str, value: Any) -> None:
        client = self._provider.get_client()
        payload = json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        await client.set(self._redis_key(cache_key), payload, ex=int(self._config.cache_ttl_seconds))

    async def get_or_fetch(
        self,
        *,
        cache_key: str,
        fetch: Callable[[], Awaitable[Any]],
    ) -> Any:
        """
        Return cached value if present, else lock + fetch + cache.

        If we can't acquire the lock, wait briefly for another instance to populate.
        """
        # Fast path
        cached = await self.get(cache_key=cache_key)
        if cached is not None:
            return cached

        client = self._provider.get_client()
        lock = RedisDistributedLock(client=client)
        lock_key = self._lock_key(cache_key)

        handle = await lock.try_acquire(key=lock_key, ttl_seconds=int(self._config.lock_ttl_seconds))
        if handle is None:
            # Someone else is fetching; poll for cache population.
            return await self._wait_for_cache_or_fallback(cache_key=cache_key, fetch=fetch)

        try:
            # Re-check after acquiring lock
            cached = await self.get(cache_key=cache_key)
            if cached is not None:
                return cached

            value = await fetch()
            await self.set(cache_key=cache_key, value=value)
            return value
        finally:
            await lock.release(handle)

    async def _wait_for_cache_or_fallback(
        self,
        *,
        cache_key: str,
        fetch: Callable[[], Awaitable[Any]],
    ) -> Any:
        deadline = time.time() + float(self._config.wait_timeout_seconds)
        while time.time() < deadline:
            cached = await self.get(cache_key=cache_key)
            if cached is not None:
                return cached
            await asyncio.sleep(float(self._config.poll_interval_seconds))

        # If cache wasn't populated in time, do a best-effort fetch without locking.
        # This still won’t amplify too much because it’s rare and callers above should
        # have held the lock; but we prefer returning data over failing hard.
        logger.info("Distributed odds cache wait timed out for %s; falling back to direct fetch", cache_key)
        value = await fetch()
        try:
            await self.set(cache_key=cache_key, value=value)
        except Exception:
            pass
        return value



