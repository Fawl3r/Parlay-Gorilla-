"""Resolve a Game row from an analysis slug.

Why this exists:
- Analysis detail routes should not 404 just because a game falls outside a
  narrow "now +/- X days" window.
- We avoid reverse-parsing fragile slugs inside the route file by centralizing
  parsing + DB lookup here (SRP, testable).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, Optional, Sequence, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import Game
from app.services.sports_config import SportConfig, get_sport_config
from app.utils.nfl_week import get_week_date_range
from app.utils.timezone_utils import TimezoneNormalizer


_NFL_WEEK_SLUG_RE = re.compile(
    r"^(?P<prefix>nfl)/(?P<away>.+)-vs-(?P<home>.+)-week-(?P<week>[^-]+)-(?P<year>\d{4})$",
    re.IGNORECASE,
)

_DATE_SLUG_RE = re.compile(
    r"^(?P<prefix>[a-z0-9]+)/(?P<away>.+)-vs-(?P<home>.+)-(?P<date>\d{4}-\d{2}-\d{2})$",
    re.IGNORECASE,
)


def _clean_team_slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")


@dataclass(frozen=True)
class _SlugParts:
    expected_full_slug: str
    away_slug: str
    home_slug: str
    week: Optional[int]
    year: Optional[int]
    date_str: Optional[str]


class AnalysisSlugResolver:
    """Find the underlying `Game` row for an analysis slug."""

    def __init__(self, db: AsyncSession):
        self._db = db

    def normalize_full_slug(self, *, sport_identifier: str, slug: str) -> str:
        """
        Normalize an incoming slug into canonical form that includes the sport prefix.

        Examples:
        - sport=nfl, slug=bears-vs-packers-week-1-2025 -> nfl/bears-vs-packers-week-1-2025
        - sport=nfl, slug=nfl/bears-vs-packers-week-1-2025 -> nfl/bears-vs-packers-week-1-2025
        """
        sport_config = get_sport_config(sport_identifier)
        sport_prefix = f"{sport_config.slug}/"
        slug_norm = str(slug or "").strip().lstrip("/")
        if slug_norm.lower().startswith(sport_prefix):
            return slug_norm
        return f"{sport_prefix}{slug_norm}"

    async def find_game(self, *, sport_identifier: str, slug: str) -> Optional[Game]:
        sport_config = get_sport_config(sport_identifier)
        expected_full = self.normalize_full_slug(sport_identifier=sport_identifier, slug=slug)

        parts = self._parse_parts(sport_config, expected_full)
        for window_start, window_end in self._candidate_windows(sport_config, parts):
            game = await self._find_in_window(sport_config, parts, window_start, window_end)
            if game:
                return game

        # Fallback: preserve old behavior (search a near-now window) if parsing failed.
        if parts is None:
            # Use naive UTC datetimes to stay compatible with SQLite (timezone handling is limited).
            now = datetime.utcnow()
            fallback_start = now - timedelta(hours=48)
            fallback_end = now + timedelta(days=int(getattr(sport_config, "lookahead_days", 7) or 7))
            return await self._find_by_slug_recompute(
                sport_config=sport_config,
                expected_full_slug=expected_full,
                window_start=fallback_start,
                window_end=fallback_end,
            )

        return None

    def _parse_parts(self, sport_config: SportConfig, expected_full_slug: str) -> Optional[_SlugParts]:
        # NFL canonical week slug: nfl/{away}-vs-{home}-week-{week}-{year}
        if sport_config.code == "NFL":
            match = _NFL_WEEK_SLUG_RE.match(expected_full_slug)
            if match:
                week_raw = (match.group("week") or "").strip()
                year_raw = (match.group("year") or "").strip()
                week = int(week_raw) if week_raw.isdigit() else None
                # Defensive: tolerate invalid week tokens (e.g., "None" from older clients)
                # by treating them as "unknown week" and falling back to a wider time window
                # + team-name matching.
                if week is not None and (week < 1 or week > 25):
                    week = None
                year = int(year_raw) if year_raw.isdigit() else None
                return _SlugParts(
                    expected_full_slug=expected_full_slug,
                    away_slug=str(match.group("away") or ""),
                    home_slug=str(match.group("home") or ""),
                    week=week,
                    year=year,
                    date_str=None,
                )

        # Date slug: {sport}/{away}-vs-{home}-{YYYY-MM-DD}
        match = _DATE_SLUG_RE.match(expected_full_slug)
        if match:
            return _SlugParts(
                expected_full_slug=expected_full_slug,
                away_slug=str(match.group("away") or ""),
                home_slug=str(match.group("home") or ""),
                week=None,
                year=None,
                date_str=str(match.group("date") or ""),
            )

        return None

    def _candidate_windows(
        self, sport_config: SportConfig, parts: Optional[_SlugParts]
    ) -> Sequence[Tuple[datetime, datetime]]:
        if parts is None:
            return []

        # NFL week-based window (try season_year = year and year-1 to handle January games).
        if sport_config.code == "NFL" and parts.week is not None and parts.year is not None:
            season_year_candidates = [parts.year, parts.year - 1]
            windows: list[Tuple[datetime, datetime]] = []
            for season_year in season_year_candidates:
                try:
                    week_start, week_end = get_week_date_range(parts.week, season_year)
                except Exception:
                    continue
                # Safety padding for edge cases (keep values naive for SQLite compatibility).
                windows.append((week_start - timedelta(hours=12), week_end + timedelta(hours=12)))
            return windows

        # NFL "week slug" but week is missing/invalid (e.g., `week-None-YYYY`):
        # fall back to a near-now window so we can match by team names.
        if sport_config.code == "NFL" and parts.year is not None and parts.week is None:
            now = datetime.utcnow()
            start = now - timedelta(hours=48)
            end = now + timedelta(days=int(getattr(sport_config, "lookahead_days", 7) or 7))
            return [(start, end)]

        # Date-based window.
        if parts.date_str:
            try:
                day = datetime.strptime(parts.date_str, "%Y-%m-%d").date()
            except Exception:
                return []
            start = datetime(day.year, day.month, day.day, 0, 0, 0)
            end = datetime(day.year, day.month, day.day, 23, 59, 59)
            return [(start - timedelta(hours=12), end + timedelta(hours=12))]

        return []

    async def _find_in_window(
        self, sport_config: SportConfig, parts: _SlugParts, window_start: datetime, window_end: datetime
    ) -> Optional[Game]:
        result = await self._db.execute(
            select(Game)
            .where(
                Game.sport == sport_config.code,
                Game.start_time >= window_start,
                Game.start_time <= window_end,
            )
            .order_by(Game.start_time)
            .limit(500)
        )
        games = result.scalars().all()
        if not games:
            return None

        # Prefer exact slug match by recompute (strongest).
        found = await self._find_by_slug_recompute(
            sport_config=sport_config,
            expected_full_slug=parts.expected_full_slug,
            window_start=window_start,
            window_end=window_end,
        )
        if found:
            return found

        # Fallback: match by cleaned team slugs inside the window.
        expected_away = _clean_team_slug(parts.away_slug)
        expected_home = _clean_team_slug(parts.home_slug)

        for game in games:
            if _clean_team_slug(game.away_team) == expected_away and _clean_team_slug(game.home_team) == expected_home:
                return game
            # Defensive fallback: allow swapped order if a client built the slug incorrectly.
            if _clean_team_slug(game.away_team) == expected_home and _clean_team_slug(game.home_team) == expected_away:
                return game

        return None

    async def _find_by_slug_recompute(
        self,
        *,
        sport_config: SportConfig,
        expected_full_slug: str,
        window_start: datetime,
        window_end: datetime,
    ) -> Optional[Game]:
        """
        Preserve legacy behavior: scan games in a window and compare canonical slugs.

        This keeps us consistent with `app.api.routes.analysis._generate_slug`, while
        still allowing higher-level window strategies to be more precise than "now +/-".
        """
        games_result = await self._db.execute(
            select(Game)
            .where(
                Game.sport == sport_config.code,
                Game.start_time >= window_start,
                Game.start_time <= window_end,
            )
            .order_by(Game.start_time)
            .limit(500)
        )
        games = games_result.scalars().all()
        if not games:
            return None

        from app.api.routes.analysis import _generate_slug  # runtime import to avoid cycles

        for game in games:
            try:
                candidate = _generate_slug(
                    home_team=game.home_team,
                    away_team=game.away_team,
                    league=game.sport,
                    game_time=game.start_time,
                )
                if candidate == expected_full_slug:
                    return game

                # Backward compatibility: NFL date-style slugs.
                if sport_config.code == "NFL":
                    home_clean = _clean_team_slug(game.home_team)
                    away_clean = _clean_team_slug(game.away_team)
                    date_str = TimezoneNormalizer.ensure_utc(game.start_time).strftime("%Y-%m-%d")  # type: ignore[union-attr]
                    legacy = f"nfl/{away_clean}-vs-{home_clean}-{date_str}"
                    if legacy == expected_full_slug:
                        return game
            except Exception:
                continue

        return None


