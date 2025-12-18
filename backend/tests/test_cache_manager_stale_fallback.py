"""Tests for CacheManager stale fallback behavior."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.cache_manager import CacheManager


@pytest.mark.asyncio
async def test_cache_manager_returns_stale_when_no_fresh_cache():
    db = AsyncMock()

    # First query (fresh) returns nothing
    fresh_result = MagicMock()
    fresh_result.scalar_one_or_none.return_value = None

    # Second query (stale) returns an entry
    stale_entry = MagicMock()
    stale_entry.cached_parlay_data = {"legs": [], "num_legs": 0}
    stale_entry.hit_count = 0
    stale_entry.expires_at = None

    stale_result = MagicMock()
    stale_result.scalar_one_or_none.return_value = stale_entry

    db.execute = AsyncMock(side_effect=[fresh_result, stale_result])
    db.commit = AsyncMock()

    manager = CacheManager(db)
    result = await manager.get_cached_parlay(num_legs=5, risk_profile="balanced", sport="NFL", max_age_hours=6)

    assert result == {"legs": [], "num_legs": 0}
    assert stale_entry.hit_count == 1
    assert db.commit.await_count >= 1




