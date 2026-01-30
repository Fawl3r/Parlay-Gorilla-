"""
Safe Key Players builder: only allowlisted names, sport-aware roles, generic why templates.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from app.services.analysis.ugie_v2.models import KeyPlayer, KeyPlayersBlock

MAX_PER_TEAM = 5
THIN_DATA_SPORTS = frozenset({"ufc", "boxing", "mma"})
WHY_MAX_LEN = 200
MAX_METRICS_PER_PLAYER = 3
MAX_METRIC_LABEL_LEN = 12
MAX_METRIC_VALUE_LEN = 16


def _normalize_name(name: str) -> str:
    if not name or not isinstance(name, str):
        return ""
    return " ".join(name.split()).strip()


def _allowlist_set(allowed: Optional[List[str]]) -> set[str]:
    if not allowed:
        return set()
    return {_normalize_name(n).lower() for n in allowed if n}


def _is_allowlisted(name: str, allowed_player_names: List[str]) -> bool:
    if not name or not allowed_player_names:
        return False
    normalized = _normalize_name(name).lower()
    return normalized in _allowlist_set(allowed_player_names)


def _map_position_to_role(sport: str, position: str) -> str:
    """Map roster position string to display role (sport-aware)."""
    s = (sport or "").strip().lower()
    pos = (position or "").strip().upper()
    if s == "nfl" or s == "ncaaf":
        role_map = {
            "QB": "QB", "RB": "RB", "WR": "WR", "TE": "TE",
            "OL": "OL", "OT": "OL", "OG": "OL", "C": "OL",
            "EDGE": "EDGE", "DE": "EDGE", "DT": "DT", "NT": "DT",
            "LB": "LB", "ILB": "LB", "OLB": "LB",
            "CB": "CB", "S": "S", "SS": "S", "FS": "S", "DB": "CB",
        }
        return role_map.get(pos, "Player")
    if s in ("nba", "wnba", "ncaab"):
        if "G" in pos or "GUARD" in pos:
            return "Guard"
        if "F" in pos or "FORWARD" in pos or "WING" in pos:
            return "Wing"
        if "C" in pos or "CENTER" in pos or "BIG" in pos:
            return "Big"
        return "Player"
    if s == "mlb":
        if "P" in pos or "SP" in pos or "RP" in pos:
            return "SP" if "SP" in pos or "START" in pos else "RP"
        if "1B" in pos or "2B" in pos or "3B" in pos or "SS" in pos or "IF" in pos:
            return "Slugger"
        if "CF" in pos or "LF" in pos or "RF" in pos or "OF" in pos:
            return "Leadoff" if pos.startswith("L") else "Slugger"
        return "Player"
    if s == "nhl":
        if "G" in pos or "GOALIE" in pos:
            return "Goalie"
        if "D" in pos or "DEFENSE" in pos:
            return "Top Pair D"
        return "Top Line F"
    if s in ("soccer", "football", "epl", "mls", "laliga", "ucl"):
        pos_lower = pos.lower()
        if "goalkeeper" in pos_lower or "gk" in pos_lower:
            return "Goalkeeper"
        if "striker" in pos_lower or "forward" in pos_lower or "cf" in pos_lower:
            return "Striker"
        if "winger" in pos_lower or "wing" in pos_lower:
            return "Winger"
        if "midfielder" in pos_lower or "mid" in pos_lower:
            return "Midfielder"
        if "defender" in pos_lower or "def" in pos_lower:
            return "Defender"
        return "Player"
    return "Player"


def _is_primary_role(sport: str, role: str) -> bool:
    """True if role is primary (QB, SP, Goalie, Striker) for impact=High."""
    s = (sport or "").strip().lower()
    r = (role or "").strip()
    if s in ("nfl", "ncaaf") and r == "QB":
        return True
    if s == "mlb" and r == "SP":
        return True
    if s == "nhl" and "Goalie" in r:
        return True
    if s in ("soccer", "football", "epl", "mls", "laliga", "ucl"):
        if "Striker" in r or "Goalkeeper" in r:
            return True
    return False


def _why_template(sport: str, role: str, team_side: Literal["home", "away"]) -> str:
    """Generic why template: no other player names."""
    s = (sport or "").strip().lower()
    r = (role or "Player").strip()
    if s in ("nfl", "ncaaf"):
        if r == "QB":
            return "Passing efficiency is central to this matchup. If protection holds, this player can drive early scoring."
        if r in ("RB", "WR", "TE"):
            return "Usage and red-zone role drive scoring upside in this script."
        return "Unit impact and matchup fit matter for this side."
    if s == "mlb":
        if r == "SP":
            return "The starting pitcher sets the run environment. Command and contact suppression are the swing factors."
        if r == "RP":
            return "Late-inning leverage can flip the script if the game is close."
        return "Lineup spot and platoon fit affect run expectancy."
    if s == "nhl":
        if "Goalie" in r:
            return "Goaltending is the primary swing factor; save percentage and high-danger stops drive outcomes."
        return "Top-unit usage and matchup deployment drive scoring probability."
    if s in ("soccer", "football", "epl", "mls", "laliga", "ucl"):
        if "Striker" in r:
            return "Chance conversion is decisive in tight matches. Quality looks in the box raise scoring probability."
        if "Goalkeeper" in r:
            return "Shot-stopping and distribution set the baseline for this side."
        if "Midfielder" in r or "Winger" in r:
            return "Control and chance creation in the middle third drive expected goals."
        return "Defensive shape and set-piece threat matter for this matchup."
    if s in ("nba", "wnba", "ncaab"):
        if r in ("Guard", "Wing"):
            return "Usage and efficiency in primary actions drive scoring and pace."
        return "Matchup fit and role in the rotation affect the spread and total."
    return "Role and matchup context are key swing factors for this game."


def _safe_metrics_list(raw: Any) -> List[Dict[str, str]]:
    """Return list of {label, value} strings only; max 3, label ≤12 chars, value ≤16 chars."""
    if not isinstance(raw, list):
        return []
    out: List[Dict[str, str]] = []
    for m in raw[:MAX_METRICS_PER_PLAYER]:
        if not isinstance(m, dict):
            continue
        label = m.get("label") or m.get("name") or ""
        value = m.get("value") or m.get("stat") or ""
        if isinstance(label, str) and isinstance(value, str):
            out.append({
                "label": label[:MAX_METRIC_LABEL_LEN],
                "value": value[:MAX_METRIC_VALUE_LEN],
            })
    return out


def _candidates_from_matchup(
    matchup_data: Dict[str, Any],
    sport: str,
    allowed_player_names: List[str],
    allowlist_by_team: Optional[Dict[str, List[str]]],
) -> tuple[List[Dict], List[Dict]]:
    """
    Extract allowlisted player candidates from matchup_data (home_features/away_features).
    Returns (home_candidates, away_candidates); each candidate is {name, role?, metrics?, ...}.
    """
    home_cands: List[Dict] = []
    away_cands: List[Dict] = []
    allowset = _allowlist_set(allowed_player_names)
    for side, key in (("home", "home_features"), ("away", "away_features")):
        features = matchup_data.get(key)
        if not isinstance(features, dict):
            continue
        for list_key in ("key_players", "player_leaders", "players"):
            raw_list = features.get(list_key)
            if not isinstance(raw_list, list):
                continue
            for p in raw_list[:MAX_PER_TEAM * 2]:
                if not isinstance(p, dict):
                    continue
                name = p.get("name") or (p.get("player") or {}).get("name") if isinstance(p.get("player"), dict) else None
                if not name:
                    continue
                name = _normalize_name(str(name))
                if name.lower() not in allowset:
                    continue
                role = p.get("role") or p.get("position") or p.get("pos") or ""
                role = _map_position_to_role(sport, str(role))
                metrics = _safe_metrics_list(p.get("metrics") or p.get("stats"))
                cand = {"name": name, "role": role, "metrics": metrics}
                if side == "home":
                    home_cands.append(cand)
                else:
                    away_cands.append(cand)
    return home_cands, away_cands


def _premium_role_rank(sport: str, role: str) -> int:
    """Lower = higher priority for roster fallback order. Unknown roles get high rank."""
    s = (sport or "").strip().lower()
    r = (role or "").strip()
    if s in ("nfl", "ncaaf"):
        order = ("QB", "WR", "RB", "EDGE", "CB", "TE", "LB", "S", "DT", "OL", "Player")
        for i, ro in enumerate(order):
            if r == ro or (ro != "Player" and ro in r):
                return i
        return len(order)
    if s == "mlb":
        order = ("SP", "RP", "Slugger", "Leadoff", "Player")  # SP first, then closer/RP, then slugger
        for i, ro in enumerate(order):
            if r == ro or (ro != "Player" and ro in r):
                return i
        return len(order)
    if s in ("soccer", "football", "epl", "mls", "laliga", "ucl"):
        order = ("Striker", "Winger", "Goalkeeper", "Midfielder", "Defender", "Player")
        for i, ro in enumerate(order):
            if r == ro or (ro != "Player" and ro in r):
                return i
        return len(order)
    return 999


def _roster_fallback(
    allowlist_by_team: Dict[str, List[str]],
    positions_by_name: Dict[str, str],
    sport: str,
    allowed_player_names: List[str],
) -> tuple[List[Dict], List[Dict]]:
    """Build candidates from roster, sorted by premium role first; all allowlisted."""
    def sorted_cands(side: str) -> List[Dict]:
        names = (allowlist_by_team.get(side) or [])[:MAX_PER_TEAM * 2]
        with_roles = []
        for name in names:
            if not _is_allowlisted(name, allowed_player_names):
                continue
            role = _map_position_to_role(sport, positions_by_name.get(name, ""))
            with_roles.append((name, role))
        with_roles.sort(key=lambda x: (_premium_role_rank(sport, x[1]), x[0]))
        return [
            {"name": n, "role": r, "metrics": []}
            for n, r in with_roles[:MAX_PER_TEAM]
        ]
    return sorted_cands("home"), sorted_cands("away")


class KeyPlayersBuilder:
    """Build KeyPlayersBlock from game, sport, matchup_data, allowlist; never emit non-allowlisted names."""

    def build(
        self,
        game: Any,
        sport: str,
        matchup_data: Dict[str, Any],
        allowed_player_names: Optional[List[str]],
        *,
        allowlist_by_team: Optional[Dict[str, List[str]]] = None,
        positions_by_name: Optional[Dict[str, str]] = None,
        redaction_count: Optional[int] = None,
        updated_at: Optional[str] = None,
    ) -> KeyPlayersBlock:
        sport_norm = (sport or "").strip().lower()
        if sport_norm in THIN_DATA_SPORTS:
            return KeyPlayersBlock(
                status="unavailable",
                reason="thin_data_sport",
                players=[],
                allowlist_source="roster_current_matchup_teams",
                updated_at=updated_at,
            )
        if not allowed_player_names or len(allowed_player_names) == 0:
            return KeyPlayersBlock(
                status="unavailable",
                reason="roster_missing_or_empty",
                players=[],
                allowlist_source="roster_current_matchup_teams",
                updated_at=updated_at,
            )
        by_team = allowlist_by_team or {}
        home_list = by_team.get("home") or []
        away_list = by_team.get("away") or []
        if not home_list and not away_list:
            return KeyPlayersBlock(
                status="unavailable",
                reason="roster_missing_or_empty",
                players=[],
                allowlist_source="roster_current_matchup_teams",
                updated_at=updated_at,
            )
        if not home_list or not away_list:
            return KeyPlayersBlock(
                status="unavailable",
                reason="roster_team_mismatch",
                players=[],
                allowlist_source="roster_current_matchup_teams",
                updated_at=updated_at,
            )
        pos_by_name = positions_by_name or {}
        home_cands, away_cands = _candidates_from_matchup(
            matchup_data, sport_norm, allowed_player_names, by_team
        )
        home_stat_count = len(home_cands)
        away_stat_count = len(away_cands)
        has_strong_stat_signal = (
            (home_stat_count >= 2 and away_stat_count >= 2)
            or (home_stat_count + away_stat_count >= 3)
        )
        if not home_cands and not away_cands:
            home_cands, away_cands = _roster_fallback(
                by_team, pos_by_name, sport_norm, allowed_player_names
            )
            status = "limited"
            reason = "roster_only_no_stats"
            confidence_base = 0.6
        else:
            if has_strong_stat_signal:
                status = "available"
                reason = None
                confidence_base = 0.8
            else:
                status = "limited"
                reason = "insufficient_stat_candidates"
                confidence_base = 0.6
                home_fill, away_fill = _roster_fallback(
                    by_team, pos_by_name, sport_norm, allowed_player_names
                )
                existing_home = {c.get("name") for c in home_cands}
                existing_away = {c.get("name") for c in away_cands}
                for c in home_fill:
                    if c.get("name") not in existing_home and len(home_cands) < MAX_PER_TEAM:
                        home_cands.append(c)
                        existing_home.add(c.get("name"))
                for c in away_fill:
                    if c.get("name") not in existing_away and len(away_cands) < MAX_PER_TEAM:
                        away_cands.append(c)
                        existing_away.add(c.get("name"))
        players: List[KeyPlayer] = []
        for side, cands in (("home", home_cands[:MAX_PER_TEAM]), ("away", away_cands[:MAX_PER_TEAM])):
            for c in cands:
                name = (c.get("name") or "").strip()
                if not name or not _is_allowlisted(name, allowed_player_names):
                    continue
                role = (c.get("role") or "Player").strip()
                impact: Literal["High", "Medium"] = "High" if _is_primary_role(sport_norm, role) else "Medium"
                why = _why_template(sport_norm, role, side)
                if len(why) > WHY_MAX_LEN:
                    why = why[:WHY_MAX_LEN].rsplit(" ", 1)[0] + "."
                conf = min(0.9, confidence_base + 0.05)
                metrics = c.get("metrics")
                if not metrics:
                    metrics = None
                players.append(
                    KeyPlayer(
                        name=name,
                        team=side,
                        role=role,
                        impact=impact,
                        why=why,
                        metrics=metrics,
                        confidence=conf,
                    )
                )
        return KeyPlayersBlock(
            status=status,
            reason=reason,
            players=players,
            allowlist_source="roster_current_matchup_teams",
            updated_at=updated_at,
        )
