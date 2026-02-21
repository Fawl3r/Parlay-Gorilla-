"""Game list deduplication utilities.

The backend can ingest games from multiple sources:
- The Odds API (with markets/odds)
- ESPN schedule fallback (no odds)

When both sources are active, the DB can contain multiple `games` rows for the
same matchup/time. This service dedupes those rows for API responses and
prefers the entry with the best odds coverage.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Tuple

from app.models.game import Game
from app.services.game_match_key import CanonicalGameMatchKey
from app.services.team_name_normalizer import TeamNameNormalizer
from app.utils.timezone_utils import TimezoneNormalizer


class GamesDeduplicationService:
    """Deduplicate `Game` rows for the same matchup/start time."""

    # Real-world provider drift:
    # ESPN schedule times can differ from The Odds API commence_time by ~10–15 minutes
    # (e.g., NBA tipoffs often start at :10 or :15). We dedupe within a wider window
    # so the UI doesn't show duplicate matchups (schedule-only + odds-backed).
    _DEDUP_BUCKET_MINUTES = 30

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

        best_by_key: Dict[CanonicalGameMatchKey, Tuple[int, int, int, int, int]] = {}
        game_by_key: Dict[CanonicalGameMatchKey, Game] = {}
        order: List[CanonicalGameMatchKey] = []

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

    def _build_key(self, game: Game) -> CanonicalGameMatchKey:
        sport = str(getattr(game, "sport", "") or "").strip()
        norm_home = self._team_normalizer.normalize(str(getattr(game, "home_team", "") or ""), sport=sport)
        norm_away = self._team_normalizer.normalize(str(getattr(game, "away_team", "") or ""), sport=sport)
        team_low, team_high = (norm_home, norm_away) if norm_home <= norm_away else (norm_away, norm_home)

        start_time = getattr(game, "start_time", None)
        if isinstance(start_time, datetime):
            utc = TimezoneNormalizer.ensure_utc(start_time)
            minute_bucket = (int(utc.minute) // self._DEDUP_BUCKET_MINUTES) * self._DEDUP_BUCKET_MINUTES
            bucketed = utc.replace(minute=minute_bucket, second=0, microsecond=0)
            start_iso = bucketed.isoformat()
        else:
            # Shouldn't happen (DB column is non-null), but keep key stable if it does.
            start_iso = ""

        return (sport, team_low, team_high, start_iso)

    @staticmethod
    def _score(game: Game) -> Tuple[int, int, int, int, int]:
        # IMPORTANT (async SQLAlchemy safety):
        # Never trigger lazy-loading inside this sync scoring function.
        # In async contexts (e.g. FastAPI routes using AsyncSession), touching an unloaded
        # relationship like `game.markets` raises:
        #   "greenlet_spawn has not been called; can't call await_only() here"
        # Treat unloaded relationships as empty for scoring purposes.
        #
        # Implementation detail:
        # Use `__dict__` to check if a relationship is already loaded without ever
        # touching the instrumented attribute (which would trigger a lazy-load).
        markets_value = getattr(game, "__dict__", {}).get("markets", None)
        markets: List[object] = list(markets_value or []) if markets_value is not None else []
        markets_count = len(markets)
        odds_count = 0
        for m in markets:
            odds_value = getattr(m, "__dict__", {}).get("odds", None)
            odds_rows: List[object] = list(odds_value or []) if odds_value is not None else []
            odds_count += len(odds_rows)

        has_odds = 1 if odds_count > 0 else 0
        is_non_espn = 0 if str(getattr(game, "external_game_id", "")).startswith("espn:") else 1

        # final tie-breaker: older rows first (stable behavior), use created_at if present
        created_at = getattr(game, "created_at", None)
        created_rank = 0
        if isinstance(created_at, datetime):
            created_rank = -int(created_at.timestamp())

        return (has_odds, odds_count, markets_count, is_non_espn, created_rank)


