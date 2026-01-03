from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx

from src.site_feed import SiteFeedClient


def test_site_feed_caches_and_enforces_slug_reuse_cooldown(tmp_path, monkeypatch) -> None:
    calls = {"n": 0}

    items = [
        {"slug": "nfl/game-1", "angle": "A", "key_points": ["k1", "k2"], "risk_note": None, "cta_url": "x"},
        {"slug": "nfl/game-2", "angle": "B", "key_points": ["k1", "k2"], "risk_note": None, "cta_url": "x"},
    ]

    class FakeClient:
        def __init__(self, timeout):
            self._timeout = timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, url, headers=None):
            calls["n"] += 1
            req = httpx.Request("GET", url)
            return httpx.Response(200, json={"items": items}, request=req)

    monkeypatch.setattr(httpx, "Client", FakeClient)

    cache_path = tmp_path / "analysis_feed.json"
    now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    client = SiteFeedClient(
        analysis_feed_url="http://example.local/api/analysis-feed",
        cache_path=cache_path,
        cache_ttl_seconds=10800,
        slug_reuse_cooldown_hours=48,
        redirect_base_url="http://localhost:8000",
        ab_variants=["a", "b"],
        timeout_seconds=1.0,
    )

    first = client.get_injectable_item(now=now, posted_raw=[])
    assert first is not None
    assert first[0].slug == "nfl/game-1"

    second = client.get_injectable_item(now=now + timedelta(hours=1), posted_raw=[])
    assert second is not None
    assert second[0].slug == "nfl/game-2"

    third = client.get_injectable_item(now=now + timedelta(hours=2), posted_raw=[])
    assert third is None
    assert calls["n"] == 1  # cached within TTL

    # After TTL + cooldown, slug 1 becomes eligible again and cache is refreshed.
    later = client.get_injectable_item(now=now + timedelta(hours=49), posted_raw=[])
    assert later is not None
    assert later[0].slug == "nfl/game-1"
    assert calls["n"] == 2


