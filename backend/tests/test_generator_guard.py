"""Tests for GeneratorGuard (concurrency gate for parlay generation)."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from app.services.guards.generator_guard import GeneratorGuard


@pytest.fixture
def guard_max2():
    """Guard with max_concurrent=2 and short timeout for tests."""
    return GeneratorGuard(max_concurrent=2, acquire_timeout_s=0.5)


@pytest.mark.asyncio
async def test_concurrent_acquire_blocks_after_limit(guard_max2):
    """After acquiring max_concurrent slots, next try_acquire returns None."""
    # Use local fallback (no Redis) so we can test in-process semaphore.
    with patch.object(guard_max2._provider, "is_configured", return_value=False):
        t1 = await guard_max2.try_acquire("test", ttl_s=60)
        t2 = await guard_max2.try_acquire("test", ttl_s=60)
        t3 = await guard_max2.try_acquire("test", ttl_s=60)
    assert t1 is not None
    assert t2 is not None
    assert t3 is None
    await guard_max2.release("test", t1)
    await guard_max2.release("test", t2)


@pytest.mark.asyncio
async def test_release_restores_capacity(guard_max2):
    """Releasing a slot allows a new acquire."""
    with patch.object(guard_max2._provider, "is_configured", return_value=False):
        t1 = await guard_max2.try_acquire("test", ttl_s=60)
        t2 = await guard_max2.try_acquire("test", ttl_s=60)
        t3 = await guard_max2.try_acquire("test", ttl_s=60)
    assert t1 and t2 and t3 is None
    await guard_max2.release("test", t1)
    t4 = await guard_max2.try_acquire("test", ttl_s=60)
    assert t4 is not None
    await guard_max2.release("test", t2)
    await guard_max2.release("test", t4)


@pytest.mark.asyncio
async def test_redis_down_fallback_uses_local_semaphore():
    """When Redis is configured but acquire fails, fall back to local semaphore."""
    guard = GeneratorGuard(max_concurrent=2, acquire_timeout_s=0.2)
    # Redis "configured" but try_acquire_redis returns None (e.g. at capacity or error)
    with patch.object(guard._provider, "is_configured", return_value=True):
        with patch.object(guard, "_try_acquire_redis", return_value=None):
            token = await guard.try_acquire("test", ttl_s=60)
    # Should get a local token
    assert token is not None
    assert token.startswith("local:")
    await guard.release("test", token)


@pytest.mark.asyncio
async def test_release_idempotent_for_unknown_token(guard_max2):
    """Releasing an unknown or already-released token does not raise."""
    with patch.object(guard_max2._provider, "is_configured", return_value=False):
        t1 = await guard_max2.try_acquire("test", ttl_s=60)
    await guard_max2.release("test", t1)
    await guard_max2.release("test", t1)
    await guard_max2.release("test", "nonexistent-token")
