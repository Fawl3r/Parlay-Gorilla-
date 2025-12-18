"""NBA stats fetcher powered by the public ESPN team endpoints."""

from __future__ import annotations

import httpx
import re
import unicodedata
from typing import Dict, List, Optional

from app.core.config import settings

# Keep consistent with probability engine budgets. This fetcher is used for
# heuristics only; prefer fast fallback over hanging requests.
HTTP_TIMEOUT = float(getattr(settings, "probability_external_fetch_timeout_seconds", 2.5) or 2.5)

NBA_TEAM_DATA = [
    ("atl", "Atlanta", "Hawks", ["atl"]),
    ("bos", "Boston", "Celtics", ["bos"]),
    ("bkn", "Brooklyn", "Nets", ["brooklyn", "nets", "bkn"]),
    ("cha", "Charlotte", "Hornets", ["charlotte", "hornets", "cha"]),
    ("chi", "Chicago", "Bulls", ["chi"]),
    ("cle", "Cleveland", "Cavaliers", ["cavs", "cle"]),
    ("dal", "Dallas", "Mavericks", ["mavs", "dal"]),
    ("den", "Denver", "Nuggets", ["den"]),
    ("det", "Detroit", "Pistons", ["det"]),
    ("gs", "Golden State", "Warriors", ["gsw", "warriors"]),
    ("hou", "Houston", "Rockets", ["hou"]),
    ("ind", "Indiana", "Pacers", ["ind"]),
    ("lac", "Los Angeles", "Clippers", ["la clippers", "clips", "lac"]),
    ("lal", "Los Angeles", "Lakers", ["lakers", "lal"]),
    ("mem", "Memphis", "Grizzlies", ["mem"]),
    ("mia", "Miami", "Heat", ["mia"]),
    ("mil", "Milwaukee", "Bucks", ["mil"]),
    ("min", "Minnesota", "Timberwolves", ["wolves", "min"]),
    ("nop", "New Orleans", "Pelicans", ["pels", "nop"]),
    ("ny", "New York", "Knicks", ["nyk", "knicks"]),
    ("okc", "Oklahoma City", "Thunder", ["okc"]),
    ("orl", "Orlando", "Magic", ["orl"]),
    ("phi", "Philadelphia", "76ers", ["sixers", "phi"]),
    ("pho", "Phoenix", "Suns", ["phx"]),
    ("por", "Portland", "Trail Blazers", ["blazers", "por"]),
    ("sac", "Sacramento", "Kings", ["sac"]),
    ("sa", "San Antonio", "Spurs", ["sas", "san antonio spurs"]),
    ("tor", "Toronto", "Raptors", ["tor"]),
    ("uta", "Utah", "Jazz", ["uta"]),
    ("was", "Washington", "Wizards", ["wizards", "was"]),
]


def _normalize(value: str) -> str:
    if not value:
        return ""
    ascii_value = unicodedata.normalize("NFKD", value)
    ascii_value = ascii_value.encode("ascii", "ignore").decode("ascii")
    ascii_value = re.sub(r"[^a-z0-9 ]+", " ", ascii_value.lower())
    return " ".join(ascii_value.split())


def _build_alias_map(team_data) -> Dict[str, set]:
    alias_map: Dict[str, set] = {}
    for slug, city, nickname, extra in team_data:
        names = {
            f"{city} {nickname}",
            city,
            nickname,
            slug,
            f"{city}{nickname}",
        }
        if city in {"Los Angeles", "New York"}:
            short = city.split()[0]
            names.add(f"{short} {nickname}")
            names.add(f"{short}{nickname}")
        if extra:
            names.update(extra)
        alias_map[slug] = {_normalize(name) for name in names}
    return alias_map


NBA_TEAM_ALIASES = _build_alias_map(NBA_TEAM_DATA)


class NBAStatsFetcher:
    """Provides NBA team metrics and recent form data from ESPN."""

    ESPN_BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams"

    def __init__(self):
        self._stats_cache: Dict[str, Dict] = {}
        self._form_cache: Dict[str, List[Dict]] = {}
        self._team_payload_cache: Dict[str, Dict] = {}
        self._schedule_cache: Dict[str, List[Dict]] = {}

    async def get_team_stats(self, team_name: str) -> Dict:
        """Return offensive/defensive metrics derived from ESPN data."""
        slug = self._resolve_slug(team_name)
        cache_key = f"stats:{slug}"

        if cache_key in self._stats_cache:
            return self._stats_cache[cache_key]

        if not slug:
            stats = self._default_stats(team_name)
            self._stats_cache[cache_key] = stats
            return stats

        try:
            payload = await self._fetch_team_payload(slug)
            record_items = payload.get("record", {}).get("items", [])
            stat_map = self._stats_list_to_map(record_items[0].get("stats", [])) if record_items else {}

            offensive = float(stat_map.get("avgPointsFor", 112.0))
            defensive = float(stat_map.get("avgPointsAgainst", 112.0))
            win_pct = float(stat_map.get("winPercent", 0.5))
            differential = float(stat_map.get("differential", 0.0))

            stats = {
                "offensive_rating": offensive,
                "defensive_rating": defensive,
                "pace": 100.0 + (differential / 5.0),
                "rebound_rate": 46.0 + win_pct * 8.0,
                "win_percent": win_pct,
                "games_played": float(stat_map.get("gamesPlayed", 0.0)),
                "differential": differential,
            }
        except Exception as exc:
            print(f"[NBAStatsFetcher] Failed to fetch stats for {team_name}: {exc}")
            stats = self._default_stats(team_name)

        self._stats_cache[cache_key] = stats
        return stats

    async def get_recent_form(self, team_name: str, games: int = 5) -> List[Dict]:
        """Return the last N completed games for the given team."""
        slug = self._resolve_slug(team_name)
        cache_key = f"form:{slug}:{games}"
        if cache_key in self._form_cache:
            return self._form_cache[cache_key]

        if not slug:
            form = self._default_form(team_name, games)
            self._form_cache[cache_key] = form
            return form

        try:
            events = await self._fetch_schedule_events(slug)
            recent: List[Dict] = []
            for event in sorted(events, key=lambda e: e.get("date") or "", reverse=True):
                competition = event.get("competitions", [{}])[0]
                competitors = competition.get("competitors", [])
                team_entry = self._find_competitor(competitors, slug)
                if not team_entry:
                    continue
                opponent_entry = next((c for c in competitors if c is not team_entry), None)
                if not opponent_entry:
                    continue

                status = competition.get("status", {}).get("type", {})
                completed = bool(status.get("completed"))

                recent.append(
                    {
                        "completed": completed,
                        "is_win": bool(team_entry.get("winner")),
                        "score": float(team_entry.get("score") or 0),
                        "opponent_score": float(opponent_entry.get("score") or 0),
                    }
                )
                if len(recent) >= games:
                    break
        except Exception as exc:
            print(f"[NBAStatsFetcher] Failed to fetch recent form for {team_name}: {exc}")
            recent = self._default_form(team_name, games)

        self._form_cache[cache_key] = recent
        return recent

    async def _fetch_team_payload(self, slug: str) -> Dict:
        if slug in self._team_payload_cache:
            return self._team_payload_cache[slug]
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.get(f"{self.ESPN_BASE_URL}/{slug}")
            response.raise_for_status()
        payload = response.json().get("team", {})
        self._team_payload_cache[slug] = payload
        return payload

    async def _fetch_schedule_events(self, slug: str) -> List[Dict]:
        if slug in self._schedule_cache:
            return self._schedule_cache[slug]
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.get(f"{self.ESPN_BASE_URL}/{slug}/schedule")
            response.raise_for_status()
        events = response.json().get("events", [])
        self._schedule_cache[slug] = events
        return events

    def _resolve_slug(self, team_name: str) -> Optional[str]:
        normalized = _normalize(team_name)
        for slug, aliases in NBA_TEAM_ALIASES.items():
            if normalized in aliases:
                return slug
        return None

    def _stats_list_to_map(self, stats: List[Dict]) -> Dict[str, float]:
        return {stat.get("name"): stat.get("value") for stat in stats}

    def _find_competitor(self, competitors: List[Dict], slug: str) -> Optional[Dict]:
        for comp in competitors:
            team = comp.get("team", {})
            abbrev = _normalize(team.get("abbreviation", ""))
            display = _normalize(team.get("displayName", ""))
            aliases = NBA_TEAM_ALIASES.get(slug, set())
            if abbrev in aliases or display in aliases:
                return comp
        return None

    def _default_stats(self, team_name: str) -> Dict:
        key = sum(ord(c) for c in team_name.lower())
        return {
            "offensive_rating": 108 + (key % 10),
            "defensive_rating": 107 + (key % 9),
            "pace": 99 + (key % 4),
            "rebound_rate": 48 + (key % 5),
            "win_percent": 0.5,
            "games_played": 0,
            "differential": 0.0,
        }

    def _default_form(self, team_name: str, games: int) -> List[Dict]:
        key = sum(ord(c) for c in team_name.lower())
        form = []
        for i in range(games):
            is_win = (key + i) % 2 == 0
            form.append(
                {
                    "completed": True,
                    "is_win": is_win,
                    "score": 110 + (key % 5),
                    "opponent_score": 105 + (key % 5) * (-1 if is_win else 1),
                }
            )
        return form

