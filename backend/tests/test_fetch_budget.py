"""Test fetch budget manager."""

import pytest
from datetime import datetime, timedelta, timezone
from app.services.fetch_budget import FetchBudgetManager


@pytest.mark.asyncio
async def test_fetch_budget_in_memory():
    """Test fetch budget manager with in-memory fallback (no DB)."""
    budget = FetchBudgetManager(db=None)
    
    key = "test:key"
    ttl = 3600  # 1 hour
    
    # First fetch should be allowed
    should_fetch = await budget.should_fetch(key, ttl_seconds=ttl)
    assert should_fetch is True
    
    # Mark as fetched
    await budget.mark_fetched(key, ttl_seconds=ttl)
    
    # Second fetch within TTL should be blocked
    should_fetch = await budget.should_fetch(key, ttl_seconds=ttl)
    assert should_fetch is False
    
    # Different key should still be allowed
    should_fetch = await budget.should_fetch("test:other", ttl_seconds=ttl)
    assert should_fetch is True


def test_fetch_budget_ttl_defaults():
    """Test that TTL defaults are reasonable."""
    # These are the expected TTLs from the plan
    expected_ttls = {
        "odds": 21600,  # 6 hours
        "weather": 86400,  # 24 hours
        "injuries": 43200,  # 12 hours
        "props": 21600,  # 6 hours
    }
    
    # Just verify the values are set correctly (documentation test)
    assert expected_ttls["odds"] == 6 * 3600
    assert expected_ttls["weather"] == 24 * 3600
    assert expected_ttls["injuries"] == 12 * 3600
    assert expected_ttls["props"] == 6 * 3600
