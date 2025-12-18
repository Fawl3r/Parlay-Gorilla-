"""Debug The Odds API responses for key sports.

Run:
  python debug_odds_api_response.py
"""

from __future__ import annotations

from typing import Any

import requests

from app.core.config import settings


def _fetch_odds(sport_key: str) -> tuple[int, Any]:
    r = requests.get(
        f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds",
        params={
            "apiKey": settings.the_odds_api_key,
            "regions": "us",
            "markets": "h2h,spreads,totals",
            "oddsFormat": "american",
        },
        timeout=30,
    )
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, r.text


def main() -> None:
    sport_keys = [
        "basketball_nba",
        "icehockey_nhl",
        "americanfootball_ncaaf",
        "americanfootball_nfl",
    ]

    for sport_key in sport_keys:
        status, payload = _fetch_odds(sport_key)
        print()
        print("=" * 80)
        print(f"{sport_key} status={status}")
        if isinstance(payload, list):
            print(f"items={len(payload)}")
            if payload:
                first = payload[0] or {}
                print(f"first_commence={first.get('commence_time')}")
                print(f"first_home={first.get('home_team')}")
                print(f"first_away={first.get('away_team')}")
        else:
            text = str(payload)
            print(text[:500])


if __name__ == "__main__":
    main()




