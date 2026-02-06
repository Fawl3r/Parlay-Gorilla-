"""ESPN base URL resolution by sport/league."""

from __future__ import annotations

from typing import Optional


# ESPN API base paths (site.api.espn.com/apis/site/v2/sports/...)
_ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports"
_SPORT_PATH_MAP = {
    "nfl": "football/nfl",
    "americanfootball_nfl": "football/nfl",
    "nba": "basketball/nba",
    "basketball_nba": "basketball/nba",
    "wnba": "basketball/wnba",
    "nhl": "hockey/nhl",
    "icehockey_nhl": "hockey/nhl",
    "mlb": "baseball/mlb",
    "baseball_mlb": "baseball/mlb",
    # Soccer
    "mls": "soccer/usa.1",
    "epl": "soccer/eng.1",
    "eng.1": "soccer/eng.1",
    "ucl": "soccer/uefa.champions",
    "uefa.champions": "soccer/uefa.champions",
    "laliga": "soccer/esp.1",
    "esp.1": "soccer/esp.1",
    "seriea": "soccer/ita.1",
    "ita.1": "soccer/ita.1",
    "bundesliga": "soccer/ger.1",
    "ger.1": "soccer/ger.1",
    "soccer": "soccer/eng.1",
    "soccer_epl": "soccer/eng.1",
    "soccer_mls": "soccer/usa.1",
}


class EspnSportResolver:
    """Resolves sport/league codes to ESPN API base URLs."""

    @classmethod
    def get_base_url(cls, sport: str) -> str:
        """
        Return ESPN API base URL for the given sport/league.
        Example: get_base_url("nfl") -> "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
        """
        key = (sport or "").strip().lower()
        if not key:
            return f"{_ESPN_BASE}/football/nfl"
        if key in _SPORT_PATH_MAP:
            return f"{_ESPN_BASE}/{_SPORT_PATH_MAP[key]}"
        if "soccer" in key or "epl" in key:
            return f"{_ESPN_BASE}/soccer/eng.1"
        if "mls" in key:
            return f"{_ESPN_BASE}/soccer/usa.1"
        return f"{_ESPN_BASE}/football/nfl"
