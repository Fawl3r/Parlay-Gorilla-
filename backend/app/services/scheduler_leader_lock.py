from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

from app.services.redis.redis_client_provider import RedisClientProvider, get_redis_provider
from app.services.redis.redis_distributed_lock import RedisDistributedLock, RedisLockHandle

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SchedulerLeaderLockConfig:
    key: str = "parlay_gorilla:scheduler:leader"
    ttl_seconds: int = 60
    renew_every_seconds: int = 20


class SchedulerLeaderLock:
    """Long-lived leader lock for background scheduler (Redis-backed)."""

    def __init__(
        self,
        *,
        provider: Optional[RedisClientProvider] = None,
        config: Optional[SchedulerLeaderLockConfig] = None,
    ):
        self._provider = provider or get_redis_provider()
        self._config = config or SchedulerLeaderLockConfig()
        self._handle: Optional[RedisLockHandle] = None
        self._lock: Optional[RedisDistributedLock] = None
        self._renew_task: Optional[asyncio.Task] = None

    def is_available(self) -> bool:
        return self._provider.is_configured()

    async def try_acquire(self) -> bool:
        client = self._provider.get_client()
        self._lock = RedisDistributedLock(client=client)
        handle = await self._lock.try_acquire(key=self._config.key, ttl_seconds=int(self._config.ttl_seconds))
        if handle is None:
            return False
        self._handle = handle
        self._renew_task = asyncio.create_task(self._renew_loop())
        return True

    async def release(self) -> None:
        if self._renew_task is not None:
            self._renew_task.cancel()
            try:
                await self._renew_task
            except asyncio.CancelledError:
                pass
            except Exception:
                pass
            self._renew_task = None

        if self._lock is not None and self._handle is not None:
            await self._lock.release(self._handle)

        self._handle = None
        self._lock = None

    async def _renew_loop(self) -> None:
        assert self._lock is not None
        assert self._handle is not None
        while True:
            await asyncio.sleep(float(self._config.renew_every_seconds))
            ok = await self._lock.extend(self._handle, ttl_seconds=int(self._config.ttl_seconds))
            if not ok:
                logger.warning("Scheduler leader lock renewal failed; continuing (key=%s)", self._config.key)



