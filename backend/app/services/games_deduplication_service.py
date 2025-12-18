"""Game list deduplication utilities.

The backend can ingest games from multiple sources:
- The Odds API (with markets/odds)
- ESPN schedule fallback (no odds)

When both sources are active, the DB can contain multiple `games` rows for the
same matchup/time. This service dedupes those rows for API responses and
prefers the entry with the best odds coverage.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Tuple

from app.models.game import Game
from app.services.team_name_normalizer import TeamNameNormalizer
from app.utils.timezone_utils import TimezoneNormalizer


@dataclass(frozen=True)
class _GameMatchKey:
    sport: str
    home_team: str
    away_team: str
    start_time_iso: str


class GamesDeduplicationService:
    """Deduplicate `Game` rows for the same matchup/start time."""

    def __init__(self, *, team_normalizer: TeamNameNormalizer | None = None):
        self._team_normalizer = team_normalizer or TeamNameNormalizer()

    def dedupe(self, games: List[Game]) -> List[Game]:
        """
        Return a stable-ordered list where only the best entry per matchup/time remains.

        Selection preference (highest wins):
        - Has odds (any odds rows)
        - Higher odds count
        - Higher markets count
        - Non-ESPN external id (so OddsAPI rows win ties)
        """

        best_by_key: Dict[_GameMatchKey, Tuple[int, int, int, int, int]] = {}
        game_by_key: Dict[_GameMatchKey, Game] = {}
        order: List[_GameMatchKey] = []

        for game in games:
            key = self._build_key(game)
            score = self._score(game)

            if key not in game_by_key:
                game_by_key[key] = game
                best_by_key[key] = score
                order.append(key)
                continue

            if score > best_by_key[key]:
                game_by_key[key] = game
                best_by_key[key] = score

        return [game_by_key[k] for k in order]

    def _normalize_team(self, name: str) -> str:
        return self._team_normalizer.normalize(name)

    @staticmethod
    def _normalize_start_time(dt: datetime) -> str:
        utc = TimezoneNormalizer.ensure_utc(dt)
        # strip seconds/micros for stable matching across sources
        normalized = utc.replace(second=0, microsecond=0)
        return normalized.isoformat()

    def _build_key(self, game: Game) -> _GameMatchKey:
        return _GameMatchKey(
            sport=str(game.sport or "").strip(),
            home_team=self._normalize_team(game.home_team),
            away_team=self._normalize_team(game.away_team),
            start_time_iso=self._normalize_start_time(game.start_time),
        )

    @staticmethod
    def _score(game: Game) -> Tuple[int, int, int, int, int]:
        markets = list(getattr(game, "markets", []) or [])
        markets_count = len(markets)
        odds_count = 0
        for m in markets:
            odds_count += len(getattr(m, "odds", []) or [])

        has_odds = 1 if odds_count > 0 else 0
        is_non_espn = 0 if str(getattr(game, "external_game_id", "")).startswith("espn:") else 1

        # final tie-breaker: older rows first (stable behavior), use created_at if present
        created_at = getattr(game, "created_at", None)
        created_rank = 0
        if isinstance(created_at, datetime):
            created_rank = -int(created_at.timestamp())

        return (has_odds, odds_count, markets_count, is_non_espn, created_rank)


