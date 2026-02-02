"""
Hydrate UGIE key_players and availability for existing analyses (detail page).

When an analysis was generated before rosters/injuries existed, this service
refreshes only those blocks on first view (upcoming games, no OpenAI calls).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import Game
from app.models.game_analysis import GameAnalysis
from app.services.analysis.roster_context_builder import RosterContextBuilder
from app.services.analysis.ugie_v2.ugie_v2_builder import UgieV2Builder
from app.services.analysis.weather.weather_impact_engine import WeatherImpactEngine
from app.services.stats_scraper import StatsScraperService
from app.services.analysis.ugie_v2.allowed_names_provider import AllowedNamesProvider

logger = logging.getLogger(__name__)

GAME_WINDOW_DAYS = 7


def _game_within_window(game_row: Game) -> bool:
    """True if game start_time is within next GAME_WINDOW_DAYS."""
    start = getattr(game_row, "start_time", None)
    if not start:
        return False
    if getattr(start, "tzinfo", None) is None:
        start = start.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    return start >= now and (start - now) <= timedelta(days=GAME_WINDOW_DAYS)


def _needs_hydration(content: Dict[str, Any]) -> bool:
    """True if key_players unavailable (roster) or availability is placeholder."""
    ugie = content.get("ugie_v2") or {}
    if not ugie:
        return False
    kp = ugie.get("key_players") or {}
    if isinstance(kp, dict):
        if kp.get("status") == "unavailable" and kp.get("reason") == "roster_missing_or_empty":
            return True
    pillars = ugie.get("pillars") or {}
    av = pillars.get("availability") or {}
    why = (av.get("why_summary") or "") if isinstance(av, dict) else ""
    if "Unable to assess injury impact" in why:
        return True
    return False


async def hydrate_key_players_and_availability(
    db: AsyncSession,
    analysis_row: GameAnalysis,
    game_row: Optional[Game],
) -> Optional[Dict[str, Any]]:
    """
    If analysis needs key_players/availability and game is upcoming, warm rosters,
    fetch matchup_data, rebuild UGIE, and merge only key_players + availability.
    Returns updated analysis_content or None.
    """
    if not game_row:
        return None
    content = (analysis_row.analysis_content or {}).copy()
    if not isinstance(content, dict):
        return None
    if not _needs_hydration(content):
        return None
    if not _game_within_window(game_row):
        return None

    try:
        roster_ctx = RosterContextBuilder(db)
        await roster_ctx.ensure_rosters_for_game(game_row)
    except Exception as e:
        logger.info("UGIE hydration: roster warm failed %s", e)
        return None

    season = str((game_row.start_time or datetime.now(timezone.utc)).year)
    stats = StatsScraperService(db)
    try:
        matchup_data = await stats.get_matchup_data(
            home_team=game_row.home_team,
            away_team=game_row.away_team,
            league=game_row.sport or "",
            season=season,
            game_time=game_row.start_time or datetime.now(timezone.utc),
        )
    except Exception as e:
        logger.info("UGIE hydration: get_matchup_data failed %s", e)
        return None

    try:
        allowed_result = await AllowedNamesProvider(db).get_allowed_player_names_for_game(game_row)
    except Exception as e:
        logger.info("UGIE hydration: allowed names failed %s", e)
        return None

    draft = dict(content)
    odds_snapshot = content.get("odds_snapshot") or {}
    model_probs = content.get("model_probs") or {}
    weather_block = WeatherImpactEngine.compute(
        game_row.sport or "",
        matchup_data.get("weather"),
    )

    try:
        new_ugie = UgieV2Builder.build(
            draft=draft,
            matchup_data=matchup_data,
            game=game_row,
            odds_snapshot=odds_snapshot,
            model_probs=model_probs,
            weather_block=weather_block,
            allowed_player_names=allowed_result.all_names,
            allowlist_by_team=allowed_result.by_team,
            positions_by_name=allowed_result.positions_by_name,
            redaction_count=None,
            updated_at=allowed_result.updated_at,
        )
    except Exception as e:
        logger.warning("UGIE hydration: build failed %s", e)
        return None

    if "ugie_v2" not in content:
        content["ugie_v2"] = {}
    content["ugie_v2"]["key_players"] = new_ugie.get("key_players")
    if "pillars" not in content["ugie_v2"]:
        content["ugie_v2"]["pillars"] = {}
    content["ugie_v2"]["pillars"]["availability"] = (
        new_ugie.get("pillars") or {}
    ).get("availability")

    return content
