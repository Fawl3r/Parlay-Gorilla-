"""NHL stats fetcher leveraging public ESPN team endpoints."""

from __future__ import annotations

import httpx
import re
import unicodedata
from typing import Dict, List, Optional

HTTP_TIMEOUT = 10.0

NHL_TEAM_DATA = [
    ("ana", "Anaheim", "Ducks", []),
    ("ari", "Arizona", "Coyotes", ["yotes"]),
    ("bos", "Boston", "Bruins", []),
    ("buf", "Buffalo", "Sabres", []),
    ("cgy", "Calgary", "Flames", []),
    ("car", "Carolina", "Hurricanes", ["canes"]),
    ("cbj", "Columbus", "Blue Jackets", ["jackets", "bluejackets"]),
    ("chi", "Chicago", "Blackhawks", ["hawks"]),
    ("col", "Colorado", "Avalanche", ["avs"]),
    ("dal", "Dallas", "Stars", []),
    ("det", "Detroit", "Red Wings", ["wings"]),
    ("edm", "Edmonton", "Oilers", []),
    ("fla", "Florida", "Panthers", []),
    ("la", "Los Angeles", "Kings", ["lak"]),
    ("min", "Minnesota", "Wild", []),
    ("mtl", "Montreal", "Canadiens", ["habs"]),
    ("nj", "New Jersey", "Devils", []),
    ("nsh", "Nashville", "Predators", ["preds"]),
    ("nyi", "New York", "Islanders", ["isles"]),
    ("nyr", "New York", "Rangers", []),
    ("ott", "Ottawa", "Senators", []),
    ("phi", "Philadelphia", "Flyers", []),
    ("pit", "Pittsburgh", "Penguins", ["pens"]),
    ("sea", "Seattle", "Kraken", []),
    ("sj", "San Jose", "Sharks", []),
    ("stl", "St. Louis", "Blues", []),
    ("tb", "Tampa Bay", "Lightning", ["bolts"]),
    ("tor", "Toronto", "Maple Leafs", ["leafs"]),
    ("van", "Vancouver", "Canucks", []),
    ("vgk", "Vegas", "Golden Knights", ["las vegas", "knights", "vgk"]),
    ("wpg", "Winnipeg", "Jets", []),
    ("wsh", "Washington", "Capitals", ["caps"]),
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
        if city in {"Los Angeles", "New York", "St. Louis"}:
            short = city.split()[0]
            names.add(f"{short} {nickname}")
            names.add(f"{short}{nickname}")
        if extra:
            names.update(extra)
        alias_map[slug] = {_normalize(name) for name in names}
    return alias_map


NHL_TEAM_ALIASES = _build_alias_map(NHL_TEAM_DATA)


class NHLStatsFetcher:
    """Provides NHL team metrics and recent form data from ESPN."""

    ESPN_BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/teams"

    def __init__(self):
        self._stats_cache: Dict[str, Dict] = {}
        self._form_cache: Dict[str, List[Dict]] = {}
        self._team_payload_cache: Dict[str, Dict] = {}
        self._schedule_cache: Dict[str, List[Dict]] = {}

    async def get_team_stats(self, team_name: str) -> Dict:
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

            stats = {
                "goals_for": float(stat_map.get("avgPointsFor", 3.1)),
                "goals_against": float(stat_map.get("avgPointsAgainst", 3.0)),
                "goal_diff": float(stat_map.get("differential", 0.0)),
                "power_play_pct": float(stat_map.get("powerPlayPct", 20.0)),
                "penalty_kill_pct": float(stat_map.get("penaltyKillPct", 78.0)),
                "win_percent": float(stat_map.get("winPercent", 0.5)),
            }
        except Exception as exc:
            print(f"[NHLStatsFetcher] Failed to fetch stats for {team_name}: {exc}")
            stats = self._default_stats(team_name)

        self._stats_cache[cache_key] = stats
        return stats

    async def get_recent_form(self, team_name: str, games: int = 5) -> List[Dict]:
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
            print(f"[NHLStatsFetcher] Failed to fetch recent form for {team_name}: {exc}")
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
        for slug, aliases in NHL_TEAM_ALIASES.items():
            if normalized in aliases:
                return slug
        return None

    def _find_competitor(self, competitors: List[Dict], slug: str) -> Optional[Dict]:
        aliases = NHL_TEAM_ALIASES.get(slug, set())
        for comp in competitors:
            team = comp.get("team", {})
            abbrev = _normalize(team.get("abbreviation", ""))
            display = _normalize(team.get("displayName", ""))
            if abbrev in aliases or display in aliases:
                return comp
        return None

    def _stats_list_to_map(self, stats: List[Dict]) -> Dict[str, float]:
        return {stat.get("name"): stat.get("value") for stat in stats}

    def _default_stats(self, team_name: str) -> Dict:
        key = sum(ord(c) for c in team_name.lower())
        return {
            "goals_for": 3.0 + (key % 10) * 0.05,
            "goals_against": 2.8 + (key % 8) * 0.05,
            "goal_diff": 0.0,
            "power_play_pct": 19.0 + (key % 5),
            "penalty_kill_pct": 78.0 + (key % 4),
            "win_percent": 0.5,
        }

    def _default_form(self, team_name: str, games: int) -> List[Dict]:
        key = sum(ord(c) for c in team_name.lower())
        form = []
        for i in range(games):
            is_win = (key + i) % 3 != 0
            form.append(
                {
                    "completed": True,
                    "is_win": is_win,
                    "score": 3 + (key % 3),
                    "opponent_score": 2 + (key % 3) * (-1 if is_win else 1),
                }
            )
        return form

