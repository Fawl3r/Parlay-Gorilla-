from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RedisLockHandle:
    key: str
    token: str


class RedisDistributedLock:
    """
    Small distributed lock built on Redis `SET key value NX EX`.

    - Safe release: only deletes if the stored token matches.
    - Optional wait/poll helper for “wait for someone else to populate cache”.
    """

    def __init__(self, *, client):
        self._client = client

    async def try_acquire(self, *, key: str, ttl_seconds: int) -> Optional[RedisLockHandle]:
        token = uuid.uuid4().hex
        try:
            ok = await self._client.set(key, token.encode("utf-8"), nx=True, ex=int(ttl_seconds))
            if ok:
                return RedisLockHandle(key=key, token=token)
            return None
        except Exception as exc:
            logger.warning("Redis lock acquire failed for key=%s: %s", key, exc)
            raise

    async def release(self, handle: RedisLockHandle) -> None:
        # Lua: if value matches token, delete; else no-op
        script = """
        if redis.call("GET", KEYS[1]) == ARGV[1] then
          return redis.call("DEL", KEYS[1])
        else
          return 0
        end
        """
        try:
            await self._client.eval(script, 1, handle.key, handle.token.encode("utf-8"))
        except Exception as exc:
            logger.warning("Redis lock release failed for key=%s: %s", handle.key, exc)

    async def extend(self, handle: RedisLockHandle, *, ttl_seconds: int) -> bool:
        # Lua: if value matches token, update TTL
        script = """
        if redis.call("GET", KEYS[1]) == ARGV[1] then
          return redis.call("EXPIRE", KEYS[1], ARGV[2])
        else
          return 0
        end
        """
        try:
            res = await self._client.eval(
                script, 1, handle.key, handle.token.encode("utf-8"), int(ttl_seconds)
            )
            return bool(res)
        except Exception as exc:
            logger.warning("Redis lock extend failed for key=%s: %s", handle.key, exc)
            return False

    async def wait_until_released(self, *, key: str, timeout_seconds: float = 10.0) -> bool:
        """
        Best-effort helper: wait for lock key to disappear.
        Returns True if released before timeout, False otherwise.
        """
        deadline = time.time() + float(timeout_seconds)
        while time.time() < deadline:
            try:
                exists = await self._client.exists(key)
                if not exists:
                    return True
            except Exception:
                return False
            await asyncio.sleep(0.15)
        return False



