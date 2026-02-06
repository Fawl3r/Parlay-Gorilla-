"""Short-lived cache for candidate legs per sport/day (Redis + in-memory fallback)."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from app.services.data_fetchers.fetch_utils import InMemoryCache
from app.services.redis.redis_client_provider import RedisClientProvider, get_redis_provider

logger = logging.getLogger(__name__)

PREFIX = "candidate_legs:v1:"


def build_candidate_legs_cache_key(
    *,
    sport: str,
    date_utc: str,
    week: Optional[int],
    include_player_props: bool,
) -> str:
    """Cache key: per sport, date (UTC), week, and include_player_props."""
    week_str = str(week) if week is not None else "all"
    props = "1" if include_player_props else "0"
    return f"{PREFIX}{(sport or '').strip().upper()}:{date_utc}:{week_str}:{props}"


class CandidateLegCache:
    """
    Cache for get_candidate_legs results.

    - Prefer Redis when configured (shared across instances).
    - Fall back to in-process cache when Redis is unavailable.
    """

    def __init__(self, *, provider: Optional[RedisClientProvider] = None) -> None:
        self._provider = provider or get_redis_provider()
        self._memory = InMemoryCache()

    async def get(self, key: str) -> Optional[list]:
        """Return cached list of candidate leg dicts, or None."""
        if self._provider.is_configured():
            try:
                client = self._provider.get_client()
                raw = await client.get(key)
                if not raw:
                    return None
                data = json.loads(raw.decode("utf-8"))
                return data if isinstance(data, list) else None
            except Exception as exc:
                logger.debug("CandidateLegCache Redis get failed: %s", exc)
        try:
            return await self._memory.get(key)
        except Exception:
            return None

    async def set(self, key: str, value: list, ttl_seconds: int) -> None:
        """Store list of candidate leg dicts (JSON-serializable)."""
        if self._provider.is_configured():
            try:
                client = self._provider.get_client()
                payload = json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
                await client.set(key, payload, ex=int(ttl_seconds))
                return
            except Exception as exc:
                logger.debug("CandidateLegCache Redis set failed: %s", exc)
        try:
            await self._memory.set(key, value, ttl=int(ttl_seconds))
        except Exception:
            pass


_candidate_leg_cache: Optional[CandidateLegCache] = None


def get_candidate_leg_cache() -> CandidateLegCache:
    """Module singleton for candidate leg cache."""
    global _candidate_leg_cache
    if _candidate_leg_cache is None:
        _candidate_leg_cache = CandidateLegCache()
    return _candidate_leg_cache
