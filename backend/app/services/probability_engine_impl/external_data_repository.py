from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, date
from typing import Any, Awaitable, Callable, Dict, Iterable, List, Optional, Set, Tuple, TYPE_CHECKING

from app.core.config import settings

if TYPE_CHECKING:  # pragma: no cover
    from app.services.probability_engine_impl.base_engine import BaseProbabilityEngine


@dataclass(frozen=True)
class PrefetchSummary:
    team_stats_count: int
    recent_form_count: int
    injuries_count: int
    weather_count: int


class ExternalDataRepository:
    """
    Request-scoped cache + safe fetch wrapper for external data sources.

    This class centralizes:
    - per-call timeouts (so external APIs can't blow the request budget)
    - bounded concurrency (so we don't spawn unbounded network work)
    - caching of both successes and failures (so we don't retry in the same request)
    """

    def __init__(self, engine: "BaseProbabilityEngine"):
        self._engine = engine
        self._sem = asyncio.Semaphore(max(1, int(settings.probability_prefetch_concurrency)))
        # Prefetch state (request-scoped). We allow fetches during the explicit
        # prefetch phase, but we avoid "retrying" missing keys later during the
        # (sequential) candidate-leg evaluation loop, which can otherwise blow
        # the request budget.
        self._prefetch_mode: bool = False

        # Track which keys we *attempted* to prefetch for this request. If a key
        # is attempted but never lands in the cache (e.g. cancelled due to the
        # prefetch budget), later lookups will return defaults immediately
        # instead of triggering additional network calls.
        self._attempted_team_stats: Set[str] = set()
        self._attempted_team_form: Set[str] = set()
        self._attempted_injuries: Set[str] = set()
        self._attempted_weather: Set[Tuple[str, date]] = set()

    def is_external_fetch_enabled(self) -> bool:
        return bool(settings.probability_external_fetch_enabled)

    def is_prefetch_enabled(self) -> bool:
        return bool(settings.probability_prefetch_enabled) and self.is_external_fetch_enabled()

    def _timeout_seconds(self) -> float:
        return float(settings.probability_external_fetch_timeout_seconds)

    async def prefetch_for_games(self, games: Iterable[Any]) -> PrefetchSummary:
        """
        Prefetch auxiliary data for the given games.

        Notes:
        - Prefetch is best-effort and never raises.
        - Only fetches data that is missing from cache.
        """
        if not self.is_prefetch_enabled():
            return PrefetchSummary(0, 0, 0, 0)

        teams: Set[str] = set()
        weather_keys: Set[Tuple[str, date]] = set()
        weather_inputs: List[Tuple[str, datetime]] = []

        for game in games:
            home = getattr(game, "home_team", None)
            away = getattr(game, "away_team", None)
            if isinstance(home, str) and home.strip():
                teams.add(home)
            if isinstance(away, str) and away.strip():
                teams.add(away)

            start_time = getattr(game, "start_time", None)
            if self._engine.weather_fetcher and isinstance(start_time, datetime) and isinstance(home, str):
                key = (home.lower(), start_time.date())
                if key not in weather_keys:
                    weather_keys.add(key)
                    weather_inputs.append((home, start_time))

        tasks: List[Awaitable[Any]] = []
        team_stats_count = 0
        recent_form_count = 0
        injuries_count = 0
        weather_count = 0

        if self._engine.stats_fetcher:
            for team in teams:
                key = team.lower().strip()
                if key and key not in self._engine._team_stats_cache and key not in self._attempted_team_stats:
                    team_stats_count += 1
                    self._attempted_team_stats.add(key)
                    tasks.append(self.get_team_stats(team))
                if key and key not in self._engine._team_form_cache and key not in self._attempted_team_form:
                    recent_form_count += 1
                    self._attempted_team_form.add(key)
                    tasks.append(self.get_recent_form(team, games=5))

        if self._engine.injury_fetcher:
            for team in teams:
                key = team.lower().strip()
                if key and key not in self._engine._injury_cache and key not in self._attempted_injuries:
                    injuries_count += 1
                    self._attempted_injuries.add(key)
                    tasks.append(self.get_key_player_status(team))

        if self._engine.weather_fetcher:
            for home_team, start_time in weather_inputs:
                key = (home_team.lower().strip(), start_time.date())
                if key[0] and key not in self._engine._weather_cache and key not in self._attempted_weather:
                    weather_count += 1
                    self._attempted_weather.add(key)
                    tasks.append(self.get_weather(home_team, start_time))

        if not tasks:
            return PrefetchSummary(0, 0, 0, 0)

        # Prefetch is best-effort. Bound the total prefetch phase so slow or
        # uncancellable network calls can't stall request handling.
        #
        # Important: while we are in the prefetch phase we allow external fetches.
        # After prefetch completes, attempted-but-missing keys will *not* trigger
        # additional network work (see get_team_stats/get_recent_form/etc.).
        self._prefetch_mode = True
        try:
            prefetch_tasks = [asyncio.create_task(t) for t in tasks]
            budget = float(getattr(settings, "probability_prefetch_total_timeout_seconds", 0.0) or 0.0)
            if budget > 0:
                done, pending = await asyncio.wait(prefetch_tasks, timeout=budget)
                for task in pending:
                    task.cancel()
                # Drain cancellations best-effort, but never block request handling.
                # Some network stacks can delay cancellation; bound the drain so we
                # don't turn a "hard cap" into another hang point.
                if pending:
                    try:
                        await asyncio.wait_for(
                            asyncio.gather(*pending, return_exceptions=True),
                            timeout=1.0,
                        )
                    except asyncio.TimeoutError:
                        # Prefetch is an optimization only; abandon lingering tasks.
                        pass
                _ = done  # results are irrelevant; caches were populated by successful calls
            else:
                results = await asyncio.gather(*prefetch_tasks, return_exceptions=True)
                _ = results  # best-effort; caches were populated by the calls
        finally:
            self._prefetch_mode = False

        return PrefetchSummary(
            team_stats_count=team_stats_count,
            recent_form_count=recent_form_count,
            injuries_count=injuries_count,
            weather_count=weather_count,
        )

    async def get_team_stats(self, team_name: str) -> Optional[Dict]:
        key = team_name.lower().strip()
        if key in self._engine._team_stats_cache:
            return self._engine._team_stats_cache.get(key)
        if key in self._attempted_team_stats and not self._prefetch_mode:
            # Prefetch already tried this key; do not retry during candidate evaluation.
            self._engine._team_stats_cache[key] = None
            return None
        if not (self._engine.stats_fetcher and self.is_external_fetch_enabled()):
            self._engine._team_stats_cache[key] = None
            return None

        async def _fetch():
            return await self._engine.stats_fetcher.get_team_stats(team_name)

        stats = await self._fetch_with_timeout(_fetch, default=None)
        self._engine._team_stats_cache[key] = stats
        return stats

    async def get_recent_form(self, team_name: str, games: int = 5) -> List[Dict]:
        key = team_name.lower().strip()
        if key in self._engine._team_form_cache:
            return self._engine._team_form_cache.get(key) or []
        if key in self._attempted_team_form and not self._prefetch_mode:
            self._engine._team_form_cache[key] = []
            return []
        if not (self._engine.stats_fetcher and self.is_external_fetch_enabled()):
            self._engine._team_form_cache[key] = []
            return []

        fetcher = self._engine.stats_fetcher
        if not hasattr(fetcher, "get_recent_form"):
            self._engine._team_form_cache[key] = []
            return []

        async def _fetch():
            return await fetcher.get_recent_form(team_name, games=games)

        form = await self._fetch_with_timeout(_fetch, default=[])
        if not isinstance(form, list):
            form = []
        self._engine._team_form_cache[key] = form
        return form

    async def get_key_player_status(self, team_name: str) -> Dict:
        key = team_name.lower().strip()
        if key in self._engine._injury_cache:
            return self._engine._injury_cache.get(key) or {}
        if key in self._attempted_injuries and not self._prefetch_mode:
            self._engine._injury_cache[key] = {}
            return {}
        if not (self._engine.injury_fetcher and self.is_external_fetch_enabled()):
            self._engine._injury_cache[key] = {}
            return {}

        async def _fetch():
            return await self._engine.injury_fetcher.get_key_player_status(team_name)

        injuries = await self._fetch_with_timeout(_fetch, default={})
        if not isinstance(injuries, dict):
            injuries = {}
        self._engine._injury_cache[key] = injuries
        return injuries

    async def get_weather(self, home_team: str, game_start_time: datetime) -> Optional[Dict]:
        cache_key = (home_team.lower().strip(), game_start_time.date() if game_start_time else None)
        if cache_key in self._engine._weather_cache:
            return self._engine._weather_cache.get(cache_key)
        if cache_key in self._attempted_weather and not self._prefetch_mode:
            self._engine._weather_cache[cache_key] = None
            return None
        if not (self._engine.weather_fetcher and self.is_external_fetch_enabled()):
            self._engine._weather_cache[cache_key] = None
            return None

        async def _fetch():
            return await self._engine.weather_fetcher.get_game_weather(home_team, game_start_time)

        weather = await self._fetch_with_timeout(_fetch, default=None)
        if weather is not None and not isinstance(weather, dict):
            weather = None
        self._engine._weather_cache[cache_key] = weather
        return weather

    async def _fetch_with_timeout(
        self,
        fetch: Callable[[], Awaitable[Any]],
        default: Any,
    ) -> Any:
        if not self.is_external_fetch_enabled():
            return default

        timeout = self._timeout_seconds()
        try:
            async with self._sem:
                return await asyncio.wait_for(fetch(), timeout=timeout)
        except asyncio.CancelledError:  # pragma: no cover
            raise
        except Exception:
            return default


