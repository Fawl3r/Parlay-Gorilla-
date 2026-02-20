"""
Live WNBA route smoke test (opt-in).

This test is intentionally disabled by default and should be run manually when
valid provider keys are configured. It verifies that one real WNBA matchup can
flow through the analysis route with stats + injuries signals present.

Covers both:
- AI Selection (AI Picks / AI Parlay Builder)
- Strategy Builder (Gorilla Parlay Builder)
Both use the same /api/analysis/{league}/{slug} pipeline and the same
injuries + stats enrichment, so this smoke validates the shared path.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Optional

import pytest
from sqlalchemy import select

from app.api.routes.analysis import _generate_slug
from app.core.config import settings
from app.models.game import Game
from app.services.odds_fetcher import OddsFetcherService
from app.services.stats_scraper import StatsScraperService
from app.utils.placeholders import is_placeholder_team


RUN_LIVE_FLAG = "RUN_LIVE_WNBA_SMOKE"
ORIGINAL_GET_MATCHUP_DATA = StatsScraperService.get_matchup_data


def _is_live_enabled() -> bool:
    return os.getenv(RUN_LIVE_FLAG, "").strip().lower() in {"1", "true", "yes", "on"}


def _has_real_provider_keys() -> bool:
    odds_key = (getattr(settings, "the_odds_api_key", None) or "").strip()
    apisports_key = (getattr(settings, "api_sports_api_key", None) or "").strip()
    return bool(odds_key and odds_key.lower() != "test-key" and apisports_key)


def _pick_upcoming_wnba_game(games: list[Game]) -> Optional[Game]:
    for game in games:
        home = (getattr(game, "home_team", None) or "").strip()
        away = (getattr(game, "away_team", None) or "").strip()
        if not home or not away:
            continue
        if is_placeholder_team(home) or is_placeholder_team(away):
            continue
        return game
    return None


def _has_home_and_away_injury_signals(signals: Iterable[Any]) -> bool:
    keys = {str(item.get("key", "")).strip() for item in signals if isinstance(item, dict)}
    return {"home_injury_impact", "away_injury_impact"}.issubset(keys)


@pytest.mark.asyncio
async def test_live_wnba_analysis_route_contains_injuries_and_stats(client, db, monkeypatch):
    """
    Live smoke:
    - warms WNBA games from odds provider
    - calls analysis detail route for one upcoming WNBA matchup
    - asserts injuries + stats are present in the returned analysis payload
    """
    if not _is_live_enabled():
        pytest.skip(f"Set {RUN_LIVE_FLAG}=1 to run live WNBA route smoke.")

    if not _has_real_provider_keys():
        pytest.skip("Live WNBA smoke requires real THE_ODDS_API_KEY and API_SPORTS_API_KEY.")

    # conftest stubs matchup fetches for deterministic tests; restore real method for this live smoke.
    monkeypatch.setattr(StatsScraperService, "get_matchup_data", ORIGINAL_GET_MATCHUP_DATA)
    monkeypatch.setattr(settings, "probability_external_fetch_enabled", True, raising=False)

    fetcher = OddsFetcherService(db)
    await fetcher.get_or_fetch_games("wnba", force_refresh=True)

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    future_cutoff = now + timedelta(days=14)
    result = await db.execute(
        select(Game)
        .where(Game.sport == "WNBA")
        .where(Game.start_time >= now)
        .where(Game.start_time <= future_cutoff)
        .order_by(Game.start_time.asc())
    )
    game = _pick_upcoming_wnba_game(list(result.scalars().all()))
    if game is None:
        pytest.skip("No upcoming WNBA matchup found from odds feed.")

    full_slug = _generate_slug(
        home_team=game.home_team,
        away_team=game.away_team,
        league=game.sport,
        game_time=game.start_time,
    )
    slug_part = full_slug.split("/", 1)[1]

    response = await client.get(f"/api/analysis/wnba/{slug_part}")
    assert response.status_code == 200, response.text

    payload = response.json()
    content = payload.get("analysis_content") or {}
    generation = content.get("generation") or {}
    data_sources = generation.get("data_sources_used") or {}

    assert data_sources.get("stats") is True, "Expected WNBA stats data in analysis payload."
    assert data_sources.get("injuries") is True, "Expected home/away injuries data in analysis payload."

    model = content.get("model_win_probability") or {}
    calculation_method = str(model.get("calculation_method") or "").strip().lower()
    assert calculation_method and calculation_method != "odds_only"

    ugie = content.get("ugie_v2") or {}
    availability = (ugie.get("pillars") or {}).get("availability") or {}
    signals = availability.get("signals") or []
    assert _has_home_and_away_injury_signals(signals), (
        "Expected home_injuries/away_injuries injury impact signals in ugie_v2 payload."
    )

    enrichment = payload.get("enrichment") or {}
    if enrichment:
        home_injuries = (enrichment.get("home_team") or {}).get("injuries_summary")
        away_injuries = (enrichment.get("away_team") or {}).get("injuries_summary")
        assert home_injuries is not None, "Expected enrichment home_team.injuries_summary."
        assert away_injuries is not None, "Expected enrichment away_team.injuries_summary."
        assert (enrichment.get("key_team_stats") or []), "Expected enrichment key_team_stats for WNBA."
