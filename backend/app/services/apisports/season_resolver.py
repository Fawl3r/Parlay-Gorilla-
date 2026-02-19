"""
API-Sports season format resolver per sport.

Season format differs by sport: NBA uses YYYY-YYYY (e.g. 2024-2025),
NFL/NHL/MLB/Soccer use YYYY. Supports both "current date" and explicit
game-date resolution for cross-year seasons (e.g. Jan–Feb → previous
season start year).
"""

from __future__ import annotations

from datetime import datetime, timezone


def _normalize_dt(dt: datetime) -> datetime:
    """Return timezone-aware datetime in UTC (naive treated as UTC)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def get_season_for_sport_at_date(sport: str, dt: datetime) -> str:
    """
    Return API-Sports season string for the given sport at a specific date.

    Used for roster/standings when resolving season for a game date (e.g.
    Jan–Feb returns previous season start year for NFL/NHL/soccer).

    - NBA: YYYY-YYYY (Oct–June); Jan–June = (year-1)-year, Oct–Dec = year-(year+1).
    - NFL: YYYY; Sep–Feb in season; Jan–Feb = year-1, Sep–Dec = year.
    - NHL: YYYY; Oct–June; Jan–June = year-1, Oct–Dec = year.
    - MLB: YYYY; Apr–Oct = year; Jan–Mar = year-1, Nov–Dec = year.
    - Soccer: YYYY (start year); Aug–May; Jan–Jul = year-1, Aug–Dec = year.

    Args:
        sport: Sport key (e.g. basketball_nba, americanfootball_nfl, football).
        dt: Date to resolve season for (game date or "now").

    Returns:
        Season string for API-Sports (e.g. "2024" or "2024-2025").
    """
    sport_lower = (sport or "").lower().strip()
    d = _normalize_dt(dt)
    year = d.year
    month = d.month

    # NBA: YYYY-YYYY (starts Oct, ends June)
    if sport_lower in ("basketball_nba", "nba", "basketball"):
        if month >= 10:
            return f"{year}-{year + 1}"
        if month <= 6:
            return f"{year - 1}-{year}"
        # Jul–Sep: off-season, use upcoming season
        return f"{year}-{year + 1}"

    # WNBA: YYYY (calendar season; API-Sports basketball uses single year; season May–Sep)
    if sport_lower in ("basketball_wnba", "wnba"):
        if 5 <= month <= 9:
            return str(year)
        if month >= 10:
            return str(year)
        return str(year - 1)  # Jan–Apr: previous season

    # NFL: Sep–Feb in season; season "year" is start year
    if sport_lower in ("americanfootball_nfl", "nfl"):
        if month >= 9:
            return str(year)
        if month <= 2:
            return str(year - 1)
        return str(year - 1)  # Mar–Aug: last completed

    # NHL: Oct–June; season "year" is start year (Oct)
    if sport_lower in ("icehockey_nhl", "nhl", "hockey"):
        if month >= 10:
            return str(year)
        if month <= 6:
            return str(year - 1)
        return str(year)  # Jul–Sep: upcoming

    # MLB: Apr–Oct in season
    if sport_lower in ("baseball_mlb", "mlb", "baseball"):
        if 4 <= month <= 10:
            return str(year)
        if month <= 3:
            return str(year - 1)
        return str(year)  # Nov–Dec: just ended

    # Soccer (football): Aug–May; season identifier = start year
    if sport_lower in ("football", "mls", "epl", "laliga", "ucl", "soccer"):
        if month >= 8:
            return str(year)
        return str(year - 1)  # Jan–Jul

    # Default: single calendar year
    return str(year)


def get_season_for_sport(sport: str) -> str:
    """
    Return API-Sports season string for the given sport key (at "now" in UTC).

    Wrapper around get_season_for_sport_at_date(sport, now).
    """
    return get_season_for_sport_at_date(sport, datetime.now(timezone.utc))


def get_apisports_season(sport_slug: str, dt: datetime) -> str:
    """
    Return API-Sports season string for a sport slug at a given date.

    Resolves sport_slug to odds_key via config and delegates to get_season_for_sport_at_date.
    Cache derived seasons by (sport_slug, year) in callers if needed (e.g. 24h).
    """
    try:
        from app.services.sports_config import get_sport_config
        cfg = get_sport_config(sport_slug)
        return get_season_for_sport_at_date(cfg.odds_key, _normalize_dt(dt))
    except Exception:
        return str(_normalize_dt(dt).year)


def get_season_int_for_sport_at_date(sport: str, dt: datetime) -> int:
    """
    Return season as int for API-Sports at a specific date.
    NBA: use first year of range (e.g. 2024 for 2024-2025).
    """
    season_str = get_season_for_sport_at_date(sport, dt)
    if "-" in season_str:
        return int(season_str.split("-")[0])
    return int(season_str)


def get_season_int_for_sport(sport: str) -> int:
    """
    Return season as int for API-Sports (used by football standings).
    Wrapper around get_season_int_for_sport_at_date(sport, now).
    """
    return get_season_int_for_sport_at_date(sport, datetime.now(timezone.utc))
