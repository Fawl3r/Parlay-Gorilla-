import asyncio
from types import SimpleNamespace

from app.services import cache_invalidation


def test_clear_games_cache():
    from app.api.routes.games_response_cache import games_response_cache

    games_response_cache.set("nfl", ["cached"])  # type: ignore[arg-type]
    cache_invalidation.clear_games_cache()
    assert games_response_cache.get("nfl") is None


def test_clear_analysis_cache():
    from app.api.routes import analysis as analysis_routes

    analysis_routes._analysis_list_cache["key"] = ("data", None)
    cache_invalidation.clear_analysis_cache()
    assert analysis_routes._analysis_list_cache == {}


def test_clear_parlay_cache(monkeypatch):
    called = {}

    class FakeManager:
        def __init__(self, db):
            self.db = db

        async def clear_cache_for_params(self, sport=None, **kwargs):
            called["sport"] = sport

        def clear_memory_cache(self):
            called["memory"] = True

    monkeypatch.setattr(cache_invalidation, "CacheManager", FakeManager)

    async def run():
        await cache_invalidation.clear_parlay_cache(db=None, sport="NFL")

    asyncio.run(run())
    assert called["sport"] == "NFL"
    assert called["memory"] is True


