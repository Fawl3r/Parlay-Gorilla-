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
from app.services.game_match_key import (
    CanonicalGameMatchKey,
    get_canonical_key_from_game,
)
from app.services.team_name_normalizer import TeamNameNormalizer


class GamesDeduplicationService:
    """Deduplicate `Game` rows for the same matchup/start time."""

    _FIVE_MINUTES = 5

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
        return get_canonical_key_from_game(game, self._team_normalizer)

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


