"""
Parse API-Sports injury payload into canonical format for UGIE and injury_feature_builder.

Defensive: tolerates unknown shapes; best-effort key_players_out and unit_counts.
"""

from __future__ import annotations

from typing import Any, Dict, List

# League code (e.g. NFL) -> API-Sports sport key
LEAGUE_TO_SPORT_KEY: Dict[str, str] = {
    "NFL": "americanfootball_nfl",
    "NBA": "basketball_nba",
    "NHL": "icehockey_nhl",
    "MLB": "baseball_mlb",
    "EPL": "football",
    "LALIGA": "football",
    "MLS": "football",
    "UCL": "football",
    "SOCCER": "football",
}

# NFL position -> unit for unit_counts (simple)
NFL_POSITION_TO_UNIT: Dict[str, str] = {
    "QB": "QB",
    "RB": "RB",
    "FB": "RB",
    "WR": "WR",
    "TE": "WR",
    "T": "OL",
    "G": "OL",
    "C": "OL",
    "OT": "OL",
    "OG": "OL",
    "DE": "DL",
    "DT": "DL",
    "NT": "DL",
    "LB": "LB",
    "ILB": "LB",
    "OLB": "LB",
    "CB": "DB",
    "S": "DB",
    "SS": "DB",
    "FS": "DB",
    "DB": "DB",
}


def _nfl_position_to_unit(pos: str) -> str:
    if not pos:
        return "OTHER"
    u = pos.upper().strip()
    return NFL_POSITION_TO_UNIT.get(u, "OTHER")


def _impact_assessment(total_injured: int, unit_counts: Dict[str, int], league: str) -> str:
    """Short, non-dramatic assessment."""
    if total_injured == 0:
        return "No major injuries flagged."
    if total_injured <= 2:
        base = "Minor injury concerns."
    elif total_injured <= 5:
        base = "Moderate injury concerns."
    else:
        base = "High injury load — depth may matter."
    if league.upper() == "NFL" and unit_counts.get("QB", 0) > 0:
        return "QB availability could swing this matchup. " + base
    return base


def apisports_injury_payload_to_canonical(
    payload: Dict[str, Any],
    league: str = "NFL",
) -> Dict[str, Any]:
    """
    Convert API-Sports injury payload (response list by team) to canonical injury dict.

    Expects payload = {"response": [ { "player": {...}, "team": {...}, ... } ]}.
    Returns dict with: key_players_out, injury_summary, impact_assessment, total_injured, unit_counts.
    """
    key_players_out: List[Dict[str, Any]] = []
    unit_counts: Dict[str, int] = {}
    total_injured = 0

    raw_list = payload.get("response") if isinstance(payload, dict) else []
    if not isinstance(raw_list, list):
        return _empty_canonical(league)

    for item in raw_list:
        if not isinstance(item, dict):
            continue
        player = item.get("player") or item
        if not isinstance(player, dict):
            continue
        total_injured += 1
        name = (
            player.get("name")
            or player.get("firstname", "") + " " + player.get("lastname", "")
            or "Unknown"
        )
        if isinstance(name, dict):
            name = name.get("name") or "Unknown"
        pos = (player.get("position") or player.get("type") or "").strip() or "—"
        status = (player.get("reason") or player.get("type") or item.get("type") or "Out").strip()
        if len(key_players_out) < 5:
            key_players_out.append({"name": str(name).strip(), "position": pos, "status": status})

        if league.upper() == "NFL":
            unit = _nfl_position_to_unit(pos)
            unit_counts[unit] = unit_counts.get(unit, 0) + 1
        else:
            unit_counts["OTHER"] = unit_counts.get("OTHER", 0) + 1

    if total_injured == 0:
        return _empty_canonical(league)

    injury_summary = _build_injury_summary(key_players_out, total_injured)
    impact_assessment = _impact_assessment(total_injured, unit_counts, league)

    return {
        "key_players_out": key_players_out,
        "injury_summary": injury_summary,
        "impact_assessment": impact_assessment,
        "total_injured": total_injured,
        "unit_counts": unit_counts,
        "injury_severity_score": min(1.0, total_injured / 10.0),
    }


def _build_injury_summary(key_players_out: List[Dict[str, Any]], total_injured: int) -> str:
    if key_players_out:
        names = [p.get("name", "Unknown") for p in key_players_out[:5]]
        if total_injured > 5:
            return f"{total_injured} key players out: {', '.join(names)}, and {total_injured - 5} more."
        return f"Key players out: {', '.join(names)}."
    return f"{total_injured} player(s) listed on injury report."


def _empty_canonical(league: str) -> Dict[str, Any]:
    return {
        "key_players_out": [],
        "injury_summary": "No significant injuries reported.",
        "impact_assessment": "No major injuries flagged.",
        "total_injured": 0,
        "unit_counts": {},
        "injury_severity_score": 0.0,
    }
