import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from unittest.mock import AsyncMock

import pytest

from app.core.config import settings
from app.services.probability_engine_impl.external_data_repository import ExternalDataRepository


@dataclass(frozen=True)
class _GameStub:
    home_team: str
    away_team: str
    start_time: datetime


class _EngineStub:
    def __init__(self, *, stats_fetcher=None, weather_fetcher=None, injury_fetcher=None, db=None):
        self.stats_fetcher = stats_fetcher
        self.weather_fetcher = weather_fetcher
        self.injury_fetcher = injury_fetcher
        self.db = db  # ExternalDataRepository checks engine.db for API-Sports integration

        # Caches expected by ExternalDataRepository
        self._team_stats_cache = {}
        self._team_form_cache = {}
        self._weather_cache = {}
        self._injury_cache = {}


@pytest.mark.asyncio
async def test_external_repo_fetch_times_out(monkeypatch):
    """ExternalDataRepository should return defaults quickly when fetch exceeds timeout."""
    monkeypatch.setattr(settings, "probability_external_fetch_enabled", True, raising=False)
    monkeypatch.setattr(settings, "probability_prefetch_enabled", True, raising=False)
    monkeypatch.setattr(settings, "probability_prefetch_concurrency", 4, raising=False)
    monkeypatch.setattr(settings, "probability_external_fetch_timeout_seconds", 0.02, raising=False)
    monkeypatch.setattr(settings, "probability_prefetch_total_timeout_seconds", 0.2, raising=False)

    async def slow_stats(_team: str):
        await asyncio.sleep(0.5)
        return {"wins": 10, "losses": 7}

    stats_fetcher = AsyncMock()
    stats_fetcher.get_team_stats.side_effect = slow_stats
    stats_fetcher.get_recent_form.side_effect = slow_stats  # not used by get_team_stats test

    engine = _EngineStub(stats_fetcher=stats_fetcher)
    repo = ExternalDataRepository(engine)

    started = asyncio.get_running_loop().time()
    result = await repo.get_team_stats("Some Team")
    elapsed = asyncio.get_running_loop().time() - started

    assert result is None
    assert elapsed < 0.2  # should be bounded by per-call timeout, not by slow_stats()


@pytest.mark.asyncio
async def test_prefetch_attempted_keys_are_not_retried_outside_prefetch(monkeypatch):
    """
    If prefetch is cancelled before a key is cached, later reads should not
    trigger another external call during candidate evaluation.
    """
    monkeypatch.setattr(settings, "probability_external_fetch_enabled", True, raising=False)
    monkeypatch.setattr(settings, "probability_prefetch_enabled", True, raising=False)
    monkeypatch.setattr(settings, "probability_prefetch_concurrency", 1, raising=False)
    monkeypatch.setattr(settings, "probability_external_fetch_timeout_seconds", 5.0, raising=False)
    monkeypatch.setattr(settings, "probability_prefetch_total_timeout_seconds", 0.01, raising=False)

    async def very_slow(*_args, **_kwargs):
        await asyncio.sleep(1.0)
        return {"wins": 10, "losses": 7}

    stats_fetcher = AsyncMock()
    stats_fetcher.get_team_stats.side_effect = very_slow
    stats_fetcher.get_recent_form.side_effect = very_slow

    engine = _EngineStub(stats_fetcher=stats_fetcher)
    repo = ExternalDataRepository(engine)

    games = [_GameStub(home_team="Team A", away_team="Team B", start_time=datetime.utcnow())]

    # Prefetch will time out almost immediately, cancelling pending tasks.
    await repo.prefetch_for_games(games)
    calls_after_prefetch = stats_fetcher.get_team_stats.await_count

    # Outside prefetch, attempted-but-missing keys should return defaults immediately and NOT retry.
    result = await repo.get_team_stats("Team A")
    assert result is None
    assert stats_fetcher.get_team_stats.await_count == calls_after_prefetch


