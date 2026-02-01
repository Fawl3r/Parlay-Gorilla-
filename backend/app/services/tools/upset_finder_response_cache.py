from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Optional

from app.services.data_fetchers.fetch_utils import InMemoryCache
from app.services.redis.redis_client_provider import RedisClientProvider, get_redis_provider

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UpsetFinderCacheDecision:
    key: str
    ttl_seconds: int


class UpsetFinderResponseCache:
    """
    Cache for /api/tools/upsets responses.

    - Prefer Redis when configured (shared across instances).
    - Fall back to in-process async cache when Redis is unavailable.
    - Separate namespaces to prevent wrong-shape cache bugs:
      - tools:upsets_meta:v1:...
      - tools:upsets_full:v1:...
    """

    META_PREFIX = "tools:upsets_meta:v1:"
    FULL_PREFIX = "tools:upsets_full:v1:"

    def __init__(self, *, provider: Optional[RedisClientProvider] = None) -> None:
        self._provider = provider or get_redis_provider()
        self._memory = InMemoryCache()

    @staticmethod
    def ttl_seconds(*, sport: str, days: int) -> int:
        s = (sport or "").strip().lower()
        if s == "all":
            return 60
        if int(days or 0) > 14:
            return 45
        return 90

    @staticmethod
    def meta_key(
        *,
        sport: str,
        days: int,
        min_edge: float,
        max_results: int,
        min_underdog_odds: int,
        entitlement: str,
    ) -> str:
        safe = lambda v: str(v).strip().lower()
        return (
            f"{UpsetFinderResponseCache.META_PREFIX}"
            f"{safe(sport)}:{int(days)}:{float(min_edge)}:{int(max_results)}:{int(min_underdog_odds)}:{safe(entitlement)}"
        )

    @staticmethod
    def full_key(
        *,
        sport: str,
        days: int,
        min_edge: float,
        max_results: int,
        min_underdog_odds: int,
        entitlement: str,
    ) -> str:
        safe = lambda v: str(v).strip().lower()
        return (
            f"{UpsetFinderResponseCache.FULL_PREFIX}"
            f"{safe(sport)}:{int(days)}:{float(min_edge)}:{int(max_results)}:{int(min_underdog_odds)}:{safe(entitlement)}"
        )

    async def get_json(self, *, key: str) -> Optional[Any]:
        if self._provider.is_configured():
            try:
                client = self._provider.get_client()
                raw = await client.get(key)
                if not raw:
                    return None
                return json.loads(raw.decode("utf-8"))
            except Exception as exc:
                logger.debug("UpsetFinderResponseCache Redis get failed: %s", exc)
        try:
            return await self._memory.get(key)
        except Exception:
            return None

    async def set_json(self, *, key: str, value: Any, ttl_seconds: int) -> None:
        if self._provider.is_configured():
            try:
                client = self._provider.get_client()
                payload = json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
                await client.set(key, payload, ex=int(ttl_seconds))
                return
            except Exception as exc:
                logger.debug("UpsetFinderResponseCache Redis set failed: %s", exc)
        try:
            await self._memory.set(key, value, ttl=int(ttl_seconds))
        except Exception:
            pass

    async def get_or_compute_json(
        self,
        *,
        key: str,
        ttl_seconds: int,
        force_refresh: bool,
        compute: Callable[[], Awaitable[Any]],
    ) -> tuple[Any, bool]:
        """
        Returns (value, cache_hit).
        `force_refresh=True` bypasses cache read but still writes.
        """
        if not force_refresh:
            cached = await self.get_json(key=key)
            if cached is not None:
                return (cached, True)

        value = await compute()
        await self.set_json(key=key, value=value, ttl_seconds=ttl_seconds)
        return (value, False)


# Module singleton so in-memory fallback persists across requests (incl tests)
upset_finder_response_cache = UpsetFinderResponseCache()

