"""Canonical game match key: single source of truth for dedupe and write-path matching.

Used by OddsAPI datastore, ESPN schedule service, games deduplication service, and
migrations. Key = (sport, team_low, team_high, start_time_iso_5min_bucket) so that
home/away order is irrelevant and 1–4 minute start-time drift maps to the same key.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple

from app.models.game import Game
from app.services.team_name_normalizer import TeamNameNormalizer
from app.utils.timezone_utils import TimezoneNormalizer


FIVE_MINUTES = 5

# Canonical key: (sport, norm_team_low, norm_team_high, start_time_iso_5min_bucket)
CanonicalGameMatchKey = Tuple[str, str, str, str]

CANONICAL_KEY_SEP = "|"


def canonical_key_to_string(key: CanonicalGameMatchKey) -> str:
    """Serialize canonical key for DB storage (games.canonical_match_key)."""
    return CANONICAL_KEY_SEP.join(key)


def normalize_start_time_to_5min_bucket(dt: datetime) -> str:
    """Floor start_time to 5-minute bucket (UTC) and return ISO string."""
    utc = TimezoneNormalizer.ensure_utc(dt)
    minute_bucket = (int(utc.minute) // FIVE_MINUTES) * FIVE_MINUTES
    normalized = utc.replace(minute=minute_bucket, second=0, microsecond=0)
    return normalized.isoformat()


def build_canonical_key(
    sport: str,
    home_team: str,
    away_team: str,
    start_time: datetime,
    *,
    team_normalizer: Optional[TeamNameNormalizer] = None,
    sport_for_normalizer: Optional[str] = None,
) -> CanonicalGameMatchKey:
    """Build order-insensitive canonical key from (sport, home, away, start_time)."""
    normalizer = team_normalizer or TeamNameNormalizer()
    sport = (sport or "").strip()
    norm_home = normalizer.normalize(home_team, sport=sport_for_normalizer or sport)
    norm_away = normalizer.normalize(away_team, sport=sport_for_normalizer or sport)
    team_low, team_high = (norm_home, norm_away) if norm_home <= norm_away else (norm_away, norm_home)
    start_iso = normalize_start_time_to_5min_bucket(start_time)
    return (sport, team_low, team_high, start_iso)


def get_canonical_key_from_game(
    game: Game,
    team_normalizer: Optional[TeamNameNormalizer] = None,
) -> CanonicalGameMatchKey:
    """Build canonical key from a Game ORM instance."""
    normalizer = team_normalizer or TeamNameNormalizer()
    sport = str(game.sport or "").strip()
    return build_canonical_key(
        sport,
        game.home_team or "",
        game.away_team or "",
        game.start_time,
        team_normalizer=normalizer,
        sport_for_normalizer=sport,
    )
