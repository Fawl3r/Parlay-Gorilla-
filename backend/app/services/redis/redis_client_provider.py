from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RedisClientConfig:
    url: str


class RedisClientProvider:
    """
    Lazily creates an async Redis client.

    - Uses `settings.redis_url`
    - Fails open: if Redis is unreachable, callers can catch and fall back.
    """

    def __init__(self, *, config: Optional[RedisClientConfig] = None):
        self._config = config or RedisClientConfig(url=settings.redis_url)
        self._client = None

    def is_configured(self) -> bool:
        return bool((self._config.url or "").strip())

    def get_client(self):
        """
        Return a singleton `redis.asyncio.Redis` instance.

        Import is lazy to avoid adding redis as a hard import cost for code paths
        that don't use caching.
        """

        if self._client is not None:
            return self._client

        if not self.is_configured():
            raise RuntimeError("Redis is not configured (missing REDIS_URL)")

        try:
            import redis.asyncio as redis_async

            # `decode_responses=False` → we store bytes for JSON payloads.
            self._client = redis_async.from_url(self._config.url, decode_responses=False)
            return self._client
        except Exception as exc:
            logger.warning("Failed to initialize Redis client: %s", exc)
            raise


# Global provider (simple DI hook)
_global_provider: Optional[RedisClientProvider] = None


def get_redis_provider() -> RedisClientProvider:
    global _global_provider
    if _global_provider is None:
        _global_provider = RedisClientProvider()
    return _global_provider



