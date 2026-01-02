"""ESPN scoreboard schedule fallback for games listing.

When The Odds API quota is exhausted (or odds are temporarily unavailable),
we still want to show users the full slate of games for NBA/NHL/NCAAF/etc.

This service pulls upcoming games from ESPN's public scoreboard endpoints and
stores them in `games` with empty markets/odds.
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.game import Game
from app.models.market import Market
from app.schemas.game import GameResponse
from app.services.game_response_converter import GameResponseConverter
from app.services.games_deduplication_service import GamesDeduplicationService
from app.services.game_time_corrector import GameTimeCorrector
from app.services.game_status_normalizer import GameStatusNormalizer
from app.services.team_name_normalizer import TeamNameNormalizer
from app.services.sports_config import SportConfig
from app.utils.nfl_week import calculate_nfl_week
from app.utils.timezone_utils import TimezoneNormalizer


class EspnScheduleGamesService:
    """Fetch and persist games from ESPN scoreboard as a fallback schedule source."""

    def __init__(self, db: AsyncSession):
        self._db = db
        self._corrector = GameTimeCorrector()
        self._converter = GameResponseConverter()
        self._deduper = GamesDeduplicationService()
        self._team_normalizer = TeamNameNormalizer()

    def _normalize_team(self, name: str) -> str:
        return self._team_normalizer.normalize(name)

    def _match_key(self, *, home_team: str, away_team: str, start_time: datetime) -> tuple[str, str, str]:
        utc = TimezoneNormalizer.ensure_utc(start_time).replace(second=0, microsecond=0)
        return (self._normalize_team(home_team), self._normalize_team(away_team), utc.isoformat())

    async def ensure_upcoming_games(self, *, sport_config: SportConfig) -> int:
        """Fetch upcoming games from ESPN and upsert them into the DB.

        Returns the number of games fetched from ESPN (not the number inserted).
        """
        now = datetime.utcnow()
        start_day = now.date()
        end_day = (now + timedelta(days=sport_config.lookahead_days)).date()

        fetched: List[Dict] = []
        days = (end_day - start_day).days + 1
        for offset in range(days):
            target = start_day + timedelta(days=offset)
            day_games = await self._corrector.fetch_espn_schedule_for_date(
                target_date=target,
                sport_code=sport_config.code,
            )
            fetched.extend(day_games)

            # Very light yield; avoids starving the event loop in dev.
            await asyncio.sleep(0)

        if not fetched:
            return 0

        # Preload existing by external_game_id (ESPN IDs are stable).
        external_ids = [self._build_external_game_id(sport_config=sport_config, game=g) for g in fetched]
        existing_result = await self._db.execute(
            select(Game).where(Game.external_game_id.in_(external_ids)).where(Game.sport == sport_config.code)
        )
        existing_by_external = {g.external_game_id: g for g in existing_result.scalars().all()}

        # Also preload existing games in the same window so we don't create duplicates when an OddsAPI row
        # already exists for the same matchup/time.
        start_times = [
            TimezoneNormalizer.ensure_utc(g.get("start_time"))
            for g in fetched
            if isinstance(g.get("start_time"), datetime)
        ]
        existing_by_match: Dict[tuple[str, str, str], Game] = {}
        if start_times:
            window_start = min(start_times) - timedelta(hours=6)
            window_end = max(start_times) + timedelta(hours=6)
            candidates_result = await self._db.execute(
                select(Game)
                .where(Game.sport == sport_config.code)
                .where(Game.start_time >= window_start)
                .where(Game.start_time <= window_end)
            )
            for game in candidates_result.scalars().all():
                key = self._match_key(home_team=game.home_team, away_team=game.away_team, start_time=game.start_time)
                if key in existing_by_match:
                    current = existing_by_match[key]
                    if str(current.external_game_id).startswith("espn:") and not str(game.external_game_id).startswith("espn:"):
                        existing_by_match[key] = game
                else:
                    existing_by_match[key] = game

        for src in fetched:
            external_game_id = self._build_external_game_id(sport_config=sport_config, game=src)
            home = str(src.get("home_team") or "").strip()
            away = str(src.get("away_team") or "").strip()
            start_time = src.get("start_time")
            if not home or not away or not start_time:
                continue

            start_time = TimezoneNormalizer.ensure_utc(start_time)
            status = GameStatusNormalizer.normalize(str(src.get("status") or ""))

            game = existing_by_external.get(external_game_id)
            if game is None:
                match_key = self._match_key(home_team=home, away_team=away, start_time=start_time)
                game = existing_by_match.get(match_key)

            if game is None:
                game = Game(
                    external_game_id=external_game_id,
                    sport=sport_config.code,
                    home_team=home,
                    away_team=away,
                    start_time=start_time,
                    status=status,
                )
                self._db.add(game)
                existing_by_external[external_game_id] = game
                existing_by_match[self._match_key(home_team=home, away_team=away, start_time=start_time)] = game
            else:
                game.home_team = home
                game.away_team = away
                game.start_time = start_time
                game.status = status

        try:
            await self._db.commit()
        except Exception:
            await self._db.rollback()
            return 0

        return len(fetched)

    async def get_upcoming_games_response(self, *, sport_config: SportConfig) -> List[GameResponse]:
        """Return games for the sport in the normal API response shape."""
        now = datetime.utcnow()
        cutoff_time = now - timedelta(hours=24)
        future_cutoff = now + timedelta(days=sport_config.lookahead_days)

        result = await self._db.execute(
            select(Game)
            .where(Game.sport == sport_config.code)
            .where(Game.start_time >= cutoff_time)
            .where(Game.start_time <= future_cutoff)
            .where((Game.status.is_(None)) | (Game.status.notin_(["finished", "closed", "complete", "Final"])))
            .options(selectinload(Game.markets).selectinload(Market.odds))
            .order_by(Game.start_time)
            .limit(sport_config.max_full_games)
        )
        games = result.scalars().all()
        if games:
            return self._converter.to_response(self._deduper.dedupe(games))

        # As a last resort, return simple rows without markets.
        result = await self._db.execute(
            select(Game)
            .where(Game.sport == sport_config.code)
            .where(Game.start_time >= cutoff_time)
            .where(Game.start_time <= future_cutoff)
            .order_by(Game.start_time)
            .limit(sport_config.max_full_games)
        )
        games = result.scalars().all()
        # Dedupe without touching relationships (markets aren't loaded here).
        seen: set[tuple[str, str, str]] = set()
        deduped: List[Game] = []
        for g in games:
            k = self._match_key(home_team=g.home_team, away_team=g.away_team, start_time=g.start_time)
            if k in seen:
                continue
            seen.add(k)
            deduped.append(g)
        games = deduped
        responses: List[GameResponse] = []
        for game in games:
            responses.append(
                GameResponse.model_validate(
                    {
                        "id": str(game.id),
                        "external_game_id": game.external_game_id,
                        "sport": game.sport,
                        "home_team": game.home_team,
                        "away_team": game.away_team,
                        "start_time": TimezoneNormalizer.ensure_utc(game.start_time),
                        "status": game.status,
                        "week": calculate_nfl_week(game.start_time) if game.sport == "NFL" else None,
                        "markets": [],
                    }
                )
            )
        return responses

    @staticmethod
    def _build_external_game_id(*, sport_config: SportConfig, game: Dict) -> str:
        event_id = str(game.get("event_id") or "").strip()
        if event_id:
            return f"espn:{sport_config.slug}:{event_id}"

        # Fallback if ESPN didn't return an event id (rare): deterministic slug.
        home = str(game.get("home_team") or "").strip().lower().replace(" ", "-")
        away = str(game.get("away_team") or "").strip().lower().replace(" ", "-")
        start_time: Optional[datetime] = game.get("start_time")
        start_token = (
            TimezoneNormalizer.ensure_utc(start_time).strftime("%Y%m%d%H%M") if start_time else "unknown"
        )
        return f"espn:{sport_config.slug}:{away}-at-{home}:{start_token}"



