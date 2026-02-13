"""
APISports repair pass: fetch fixtures for dates that contain placeholder games;
match DB games by closest start_time; update only Game.home_team / Game.away_team.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import Game
from app.services.apisports.client import ApiSportsClient, get_apisports_client
from app.services.apisports.data_adapter import ApiSportsDataAdapter  # fixture_to_game_schedule
from app.services.apisports.season_resolver import get_season_int_for_sport
from app.utils.placeholders import is_placeholder_team

logger = logging.getLogger(__name__)

# Sport code (NFL, NBA) -> API-Sports key and league_id
SPORT_LEAGUE: Dict[str, Tuple[str, int]] = {
    "NFL": ("americanfootball_nfl", 1),
    "NBA": ("basketball_nba", 12),
    "NHL": ("icehockey_nhl", 57),
    "MLB": ("baseball_mlb", 1),
}


class ApiSportsRepairPass:
    """Repair placeholder team names using API-Sports fixtures for the relevant dates."""

    def __init__(self, db: AsyncSession, client: Optional[ApiSportsClient] = None):
        self._db = db
        self._client = client or get_apisports_client()

    async def repair(
        self,
        sport: str,
        placeholder_games: List[Game],
        trace_id: Optional[str] = None,
    ) -> int:
        """
        Fetch API-Sports fixtures for dates that contain placeholder_games;
        match each DB game by closest start_time (non-placeholder names); update team names.
        Returns number of games updated.
        """
        if not placeholder_games or not self._client.is_configured():
            return 0
        sport_upper = (sport or "NFL").upper()
        key_league = SPORT_LEAGUE.get(sport_upper)
        if not key_league:
            return 0
        api_sport_key, league_id = key_league
        season = get_season_int_for_sport(api_sport_key)
        dates_needed: List[str] = []
        for g in placeholder_games:
            if g.start_time:
                d = g.start_time.strftime("%Y-%m-%d")
                if d not in dates_needed:
                    dates_needed.append(d)
        if not dates_needed:
            return 0
        api_games: List[Dict[str, Any]] = []
        for date_str in dates_needed:
            # Soccer uses get_fixtures; NFL/NBA/NHL/MLB use get_games (v1)
            if api_sport_key == "football" or "football" in api_sport_key:
                data = await self._client.get_fixtures(
                    league_id=league_id,
                    from_date=date_str,
                    to_date=date_str,
                    sport=api_sport_key,
                )
            else:
                data = await self._client.get_games(
                    league_id=league_id,
                    season=str(season) if season else None,
                    date=date_str,
                    sport=api_sport_key,
                )
            if not data or not isinstance(data.get("response"), list):
                continue
            for raw in data["response"]:
                canon = ApiSportsDataAdapter.fixture_to_game_schedule(raw, api_sport_key)
                if not canon or is_placeholder_team(canon.get("home_team_name")) or is_placeholder_team(canon.get("away_team_name")):
                    continue
                api_games.append({
                    "start_time": canon.get("date"),
                    "home_team": (canon.get("home_team_name") or "").strip(),
                    "away_team": (canon.get("away_team_name") or "").strip(),
                    "season_phase": canon.get("season_phase"),
                    "stage": canon.get("stage"),
                    "round": canon.get("round"),
                })
        if not api_games:
            return 0
        updated = 0
        for game in placeholder_games:
            best = self._best_match(game, api_games)
            if best:
                game.home_team = best["home_team"]
                game.away_team = best["away_team"]
                if best.get("season_phase") is not None:
                    game.season_phase = best["season_phase"]
                if best.get("stage") is not None:
                    game.stage = best["stage"]
                if best.get("round") is not None:
                    game.round_ = best["round"]
                updated += 1
        return updated

    @staticmethod
    def _best_match(game: Game, api_games: List[Dict[str, Any]], tolerance_seconds: float = 3600 * 6) -> Optional[Dict[str, Any]]:
        """Return the API game with closest start_time within tolerance."""
        if not game.start_time:
            return None
        best: Optional[Dict[str, Any]] = None
        best_diff: Optional[float] = None
        for ag in api_games:
            st = ag.get("start_time")
            if not st:
                continue
            if hasattr(st, "timestamp"):
                ts = st.timestamp()
            else:
                continue
            diff = abs((game.start_time.replace(tzinfo=timezone.utc) if game.start_time.tzinfo is None else game.start_time).timestamp() - ts)
            if diff <= tolerance_seconds and (best_diff is None or diff < best_diff):
                best = ag
                best_diff = diff
        return best
