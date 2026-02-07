"""
Redis-backed distributed semaphore for generator endpoints (AI Picks, Custom Builder).

Limits concurrent heavy parlay generation to avoid OOM on 512MB instances.
Uses key prefix pg:guard:{name}:slots (sorted set: member=token, score=expiry).
Falls back to in-process asyncio.BoundedSemaphore when Redis is unavailable.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
import uuid
from typing import Optional

from app.core.config import settings
from app.services.redis.redis_client_provider import RedisClientProvider, get_redis_provider

logger = logging.getLogger(__name__)

KEY_PREFIX = "pg:guard"


class GeneratorGuard:
    """
    Bounds concurrency for generator endpoints (parlay suggest, parlay analyze).

    - try_acquire(name, ttl_s): returns a token str if a slot was acquired, else None.
    - release(name, token): releases the slot; must be called in finally.
    - When Redis is down, uses in-process BoundedSemaphore (per-instance only).
    """

    def __init__(
        self,
        *,
        provider: Optional[RedisClientProvider] = None,
        max_concurrent: Optional[int] = None,
        acquire_timeout_s: Optional[float] = None,
    ):
        self._provider = provider or get_redis_provider()
        self._max = max_concurrent if max_concurrent is not None else settings.generator_max_concurrent
        self._timeout_s = acquire_timeout_s if acquire_timeout_s is not None else settings.generator_acquire_timeout_s
        self._local_sem: Optional[asyncio.BoundedSemaphore] = None
        self._local_lock = threading.Lock()

    def _slots_key(self, name: str) -> str:
        return f"{KEY_PREFIX}:{name}:slots"

    def _get_local_sem(self) -> asyncio.BoundedSemaphore:
        with self._local_lock:
            if self._local_sem is None:
                self._local_sem = asyncio.BoundedSemaphore(self._max)
        return self._local_sem

    async def try_acquire(self, name: str, ttl_s: int = 180) -> Optional[str]:
        """
        Try to acquire one slot. Returns a token if acquired, None if at capacity or timeout.

        When using Redis, waits up to generator_acquire_timeout_s for a slot.
        """
        if self._provider.is_configured():
            token = await self._try_acquire_redis(name, ttl_s)
            if token is not None:
                return token
            logger.debug("GeneratorGuard Redis acquire at capacity or failed, using local fallback")
        return await self._try_acquire_local(name)

    async def _try_acquire_redis(self, name: str, ttl_s: int) -> Optional[str]:
        key = self._slots_key(name)
        token = uuid.uuid4().hex
        now = time.time()
        deadline = now + max(0.0, float(self._timeout_s))
        try:
            client = self._provider.get_client()
            # Lua: remove expired, then if count < max add token with score = now+ttl
            acquire_script = """
            local now = tonumber(ARGV[1])
            local ttl = tonumber(ARGV[2])
            local max_slots = tonumber(ARGV[4])
            redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', now)
            local count = redis.call('ZCARD', KEYS[1])
            if count < max_slots then
                redis.call('ZADD', KEYS[1], now + ttl, ARGV[3])
                return 1
            end
            return 0
            """
            token_arg = token.encode("utf-8") if not getattr(client, "decode_responses", True) else token
            while time.time() < deadline:
                result = await client.eval(
                    acquire_script,
                    1,
                    key,
                    str(now),
                    str(ttl_s),
                    token_arg,
                    str(self._max),
                )
                if result == 1:
                    return token
                await asyncio.sleep(0.05)
                now = time.time()
            return None
        except Exception as exc:
            logger.warning("GeneratorGuard Redis acquire failed for name=%s: %s", name, exc)
            return None

    async def _try_acquire_local(self, name: str) -> Optional[str]:
        sem = self._get_local_sem()
        try:
            await asyncio.wait_for(sem.acquire(), timeout=max(0.001, self._timeout_s))
            return f"local:{name}:{uuid.uuid4().hex}"
        except asyncio.TimeoutError:
            return None

    async def release(self, name: str, token: str) -> None:
        """Release a slot. No-op if token is invalid or already released."""
        if token.startswith("local:"):
            sem = self._get_local_sem()
            try:
                sem.release()
            except ValueError:
                pass
            return
        if not self._provider.is_configured():
            return
        key = self._slots_key(name)
        try:
            client = self._provider.get_client()
            token_arg = token.encode("utf-8") if not getattr(client, "decode_responses", True) else token
            removed = await client.zrem(key, token_arg)
            if not removed:
                logger.debug("GeneratorGuard release: token not found (may have expired) name=%s", name)
        except Exception as exc:
            logger.warning("GeneratorGuard Redis release failed for name=%s: %s", name, exc)


_guard_instance: Optional[GeneratorGuard] = None


def get_generator_guard() -> GeneratorGuard:
    """Return the shared GeneratorGuard instance."""
    global _guard_instance
    if _guard_instance is None:
        _guard_instance = GeneratorGuard()
    return _guard_instance
