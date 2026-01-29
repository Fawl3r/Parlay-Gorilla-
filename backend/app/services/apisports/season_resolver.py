"""
API-Sports season format resolver per sport.

Season format differs by sport: NBA uses YYYY-YYYY (e.g. 2024-2025),
NFL/NHL/MLB/Soccer use YYYY. Used only by the refresh job.
"""

from __future__ import annotations

from datetime import datetime, timezone


def get_season_for_sport(sport: str) -> str:
    """
    Return API-Sports season string for the given sport key.

    - NBA: YYYY-YYYY (e.g. 2024-2025) based on Oct–June season.
    - NFL, NHL, MLB, Football (soccer): YYYY (calendar year).

    Args:
        sport: Sport key (e.g. basketball_nba, americanfootball_nfl).

    Returns:
        Season string for API-Sports (e.g. "2024" or "2024-2025").
    """
    sport_lower = (sport or "").lower().strip()
    now = datetime.now(timezone.utc)
    year = now.year

    # NBA season: e.g. 2024-2025 (starts Oct, ends June)
    if sport_lower in ("basketball_nba", "nba", "basketball"):
        if now.month >= 10:
            return f"{year}-{year + 1}"
        return f"{year - 1}-{year}"

    # All others: single year
    return str(year)


def get_season_int_for_sport(sport: str) -> int:
    """
    Return season as int for API-Sports (used by football standings).
    NBA: use first year of range (e.g. 2024 for 2024-2025).
    """
    season_str = get_season_for_sport(sport)
    if "-" in season_str:
        return int(season_str.split("-")[0])
    return int(season_str)
