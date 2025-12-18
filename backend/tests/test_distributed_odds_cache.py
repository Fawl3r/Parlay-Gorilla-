import asyncio
import time
from dataclasses import dataclass
from typing import Any, Optional

import pytest

from app.services.odds_api.distributed_odds_api_cache import DistributedOddsApiCache, DistributedOddsApiCacheConfig
from app.services.scheduler_leader_lock import SchedulerLeaderLock, SchedulerLeaderLockConfig


class InMemoryAsyncRedis:
    def __init__(self):
        self._store: dict[str, tuple[bytes, float]] = {}

    def _now(self) -> float:
        return time.time()

    def _purge_if_expired(self, key: str) -> None:
        item = self._store.get(key)
        if item is None:
            return
        _, expires_at = item
        if expires_at and expires_at <= self._now():
            self._store.pop(key, None)

    async def get(self, key: str) -> Optional[bytes]:
        self._purge_if_expired(key)
        item = self._store.get(key)
        return None if item is None else item[0]

    async def set(self, key: str, value: bytes, nx: bool = False, ex: Optional[int] = None):
        self._purge_if_expired(key)
        if nx and key in self._store:
            return None
        ttl = int(ex or 0)
        expires_at = self._now() + ttl if ttl > 0 else 0.0
        self._store[key] = (value, expires_at)
        return True

    async def exists(self, key: str) -> int:
        self._purge_if_expired(key)
        return 1 if key in self._store else 0

    async def delete(self, key: str) -> int:
        self._purge_if_expired(key)
        existed = 1 if key in self._store else 0
        self._store.pop(key, None)
        return existed

    async def eval(self, _script: str, _numkeys: int, key: str, *args):
        # release script uses (token)
        # extend script uses (token, ttl)
        self._purge_if_expired(key)
        if len(args) == 1:
            token = args[0]
            cur = self._store.get(key)
            if cur and cur[0] == token:
                self._store.pop(key, None)
                return 1
            return 0
        if len(args) == 2:
            token = args[0]
            ttl = int(args[1])
            cur = self._store.get(key)
            if cur and cur[0] == token:
                self._store[key] = (cur[0], self._now() + ttl)
                return 1
            return 0
        return 0


@dataclass(frozen=True)
class FakeRedisProvider:
    client: InMemoryAsyncRedis

    def is_configured(self) -> bool:
        return True

    def get_client(self):
        return self.client


@pytest.mark.asyncio
async def test_distributed_odds_cache_hit_avoids_fetch():
    redis = InMemoryAsyncRedis()
    provider = FakeRedisProvider(redis)
    cache = DistributedOddsApiCache(
        provider=provider, config=DistributedOddsApiCacheConfig(cache_ttl_seconds=60, lock_ttl_seconds=5)
    )
    key = cache.build_cache_key(sport_key="nfl", regions="us", markets="h2h", odds_format="american")
    await cache.set(cache_key=key, value=[{"ok": True}])

    called = 0

    async def fetch():
        nonlocal called
        called += 1
        return [{"ok": False}]

    res = await cache.get_or_fetch(cache_key=key, fetch=fetch)
    assert res == [{"ok": True}]
    assert called == 0


@pytest.mark.asyncio
async def test_distributed_odds_cache_dedupes_concurrent_fetches():
    redis = InMemoryAsyncRedis()
    provider = FakeRedisProvider(redis)
    cache = DistributedOddsApiCache(
        provider=provider, config=DistributedOddsApiCacheConfig(cache_ttl_seconds=60, lock_ttl_seconds=5, wait_timeout_seconds=5.0)
    )
    key = cache.build_cache_key(sport_key="nba", regions="us", markets="h2h", odds_format="american")

    called = 0

    async def fetch():
        nonlocal called
        called += 1
        await asyncio.sleep(0.2)
        return [{"sport": "nba"}]

    r1, r2 = await asyncio.gather(
        cache.get_or_fetch(cache_key=key, fetch=fetch),
        cache.get_or_fetch(cache_key=key, fetch=fetch),
    )

    assert r1 == [{"sport": "nba"}]
    assert r2 == [{"sport": "nba"}]
    assert called == 1


@pytest.mark.asyncio
async def test_scheduler_leader_lock_exclusive_and_renewing():
    redis = InMemoryAsyncRedis()
    provider = FakeRedisProvider(redis)
    cfg = SchedulerLeaderLockConfig(key="leader:test", ttl_seconds=1, renew_every_seconds=0.2)

    lock1 = SchedulerLeaderLock(provider=provider, config=cfg)
    lock2 = SchedulerLeaderLock(provider=provider, config=cfg)

    assert await lock1.try_acquire() is True
    assert await lock2.try_acquire() is False

    # Wait longer than TTL; renewal should keep it alive
    await asyncio.sleep(1.3)
    assert await redis.exists(cfg.key) == 1

    await lock1.release()
    assert await redis.exists(cfg.key) == 0
    assert await lock2.try_acquire() is True
    await lock2.release()



