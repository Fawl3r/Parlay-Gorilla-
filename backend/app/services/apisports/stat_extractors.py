"""
Extract normalized team season stats from raw API-Sports JSON per sport family.

Rules: never guess fields; return only metrics present; normalize numeric types.
Percentages: 0-100 scale consistently. Provide format_display_value for UI.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


def _safe_float(val: Any) -> Optional[float]:
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _safe_int(val: Any) -> Optional[int]:
    if val is None:
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _pct_to_100(val: Any) -> Optional[float]:
    """Normalize percentage to 0-100 scale."""
    f = _safe_float(val)
    if f is None:
        return None
    if 0 <= f <= 1:
        return round(f * 100, 1)
    return round(f, 1)


def format_display_value(key: str, value: Any) -> str:
    """Format a metric value for display (no guessing; pass-through for unknown keys)."""
    if value is None:
        return "—"
    if isinstance(value, float):
        if key.endswith("_pct") or "pct" in key or "percent" in key.lower():
            return f"{value:.1f}%"
        return f"{value:.1f}" if value != int(value) else str(int(value))
    if isinstance(value, int):
        return str(value)
    return str(value)


# --- Standings-entry extractors (one team row from standings response); used when on-demand stats unavailable ---

def extract_key_stats_basketball(entry: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """From one standings entry (NBA/WNBA), return normalized key stats. Never guess missing fields."""
    out: Dict[str, Any] = {}
    if not entry or not isinstance(entry, dict):
        return out
    goals = entry.get("goalsFor") or entry.get("goals_for")
    if goals is not None:
        v = _safe_int(goals)
        if v is not None:
            out["points_for"] = v
    ga = entry.get("goalsAgainst") or entry.get("goals_against")
    if ga is not None:
        v = _safe_int(ga)
        if v is not None:
            out["points_against"] = v
    all_ = entry.get("all") or entry.get("games")
    if isinstance(all_, dict):
        w, l = all_.get("win"), all_.get("lose")
        if (vw := _safe_int(w)) is not None:
            out["wins"] = vw
        if (vl := _safe_int(l)) is not None:
            out["losses"] = vl
    return out


def extract_key_stats_football(entry: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """From one standings entry (NFL), return normalized key stats."""
    out: Dict[str, Any] = {}
    if not entry or not isinstance(entry, dict):
        return out
    goals = entry.get("goalsFor") or entry.get("goals_for")
    if goals is not None and (v := _safe_int(goals)) is not None:
        out["points_for"] = v
    ga = entry.get("goalsAgainst") or entry.get("goals_against")
    if ga is not None and (v := _safe_int(ga)) is not None:
        out["points_against"] = v
    all_ = entry.get("all") or entry.get("games")
    if isinstance(all_, dict):
        if (vw := _safe_int(all_.get("win"))) is not None:
            out["wins"] = vw
        if (vl := _safe_int(all_.get("lose"))) is not None:
            out["losses"] = vl
    if (ty := _safe_int(entry.get("total_yards"))) is not None:
        out["total_yards"] = ty
    if (py := _safe_int(entry.get("pass_yards"))) is not None:
        out["pass_yards"] = py
    if (ry := _safe_int(entry.get("rush_yards"))) is not None:
        out["rush_yards"] = ry
    return out


def extract_key_stats_hockey(entry: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """From one standings entry (NHL), return normalized key stats."""
    out: Dict[str, Any] = {}
    if not entry or not isinstance(entry, dict):
        return out
    if (gf := _safe_int(entry.get("goalsFor") or entry.get("goals_for"))) is not None:
        out["goals_for"] = gf
    if (ga := _safe_int(entry.get("goalsAgainst") or entry.get("goals_against"))) is not None:
        out["goals_against"] = ga
    all_ = entry.get("all") or entry.get("games")
    if isinstance(all_, dict):
        if (vw := _safe_int(all_.get("win"))) is not None:
            out["wins"] = vw
        if (vl := _safe_int(all_.get("lose"))) is not None:
            out["losses"] = vl
    if (sf := _safe_int(entry.get("shotsFor") or entry.get("shots_for"))) is not None:
        out["shots_for"] = sf
    if (sa := _safe_int(entry.get("shotsAgainst") or entry.get("shots_against"))) is not None:
        out["shots_against"] = sa
    return out


def extract_key_stats_baseball(entry: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """From one standings entry (MLB), return normalized key stats."""
    out: Dict[str, Any] = {}
    if not entry or not isinstance(entry, dict):
        return out
    rf = entry.get("goalsFor") or entry.get("runs_for") or entry.get("runs")
    if rf is not None and (v := _safe_int(rf)) is not None:
        out["runs_for"] = v
    ra = entry.get("goalsAgainst") or entry.get("runs_against")
    if ra is not None and (v := _safe_int(ra)) is not None:
        out["runs_against"] = v
    all_ = entry.get("all") or entry.get("games")
    if isinstance(all_, dict):
        if (vw := _safe_int(all_.get("win"))) is not None:
            out["wins"] = vw
        if (vl := _safe_int(all_.get("lose"))) is not None:
            out["losses"] = vl
    era = _safe_float(entry.get("era"))
    if era is not None:
        out["era"] = era
    avg = _safe_float(entry.get("avg"))
    if avg is not None:
        out["avg"] = avg
    return out


# --- Raw API statistics response extractors (on-demand team stats endpoint) ---

# --- Basketball (NBA / WNBA) ---

def extract_basketball_team_stats(raw: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract normalized stats from API-Sports basketball statistics response.
    Expects response.response or response to contain team/season stats.
    Returns only keys that exist; per-game values when available.
    """
    out: Dict[str, Any] = {}
    if not raw or not isinstance(raw, dict):
        return out
    resp = raw.get("response")
    if isinstance(resp, list) and resp:
        data = resp[0] if isinstance(resp[0], dict) else {}
    elif isinstance(resp, dict):
        data = resp
    else:
        data = raw
    if not data:
        return out
    # Common API-Sports basketball keys (league/season aggregates)
    games = _safe_int(data.get("games")) or _safe_int(data.get("games_played")) or 1
    if games <= 0:
        games = 1
    pts = _safe_float(data.get("points")) or _safe_float(data.get("points_for"))
    if pts is not None:
        out["points_for"] = round(pts / games, 1)
    pts_against = _safe_float(data.get("points_against"))
    if pts_against is not None:
        out["points_against"] = round(pts_against / games, 1)
    w = _safe_int(data.get("wins"))
    if w is not None:
        out["wins"] = w
    l = _safe_int(data.get("losses"))
    if l is not None:
        out["losses"] = l
    fg_pct = _pct_to_100(data.get("fg_pct")) or _pct_to_100(data.get("field_goal_pct"))
    if fg_pct is not None:
        out["fg_pct"] = fg_pct
    three_pct = _pct_to_100(data.get("three_pct")) or _pct_to_100(data.get("three_point_pct"))
    if three_pct is not None:
        out["three_pct"] = three_pct
    ft_pct = _pct_to_100(data.get("ft_pct")) or _pct_to_100(data.get("free_throw_pct"))
    if ft_pct is not None:
        out["ft_pct"] = ft_pct
    reb = _safe_float(data.get("rebounds")) or _safe_float(data.get("rebounds_per_game"))
    if reb is not None:
        out["rebounds"] = round(reb, 1) if reb >= 0 and reb < 500 else round(reb / games, 1)
    ast = _safe_float(data.get("assists")) or _safe_float(data.get("assists_per_game"))
    if ast is not None:
        out["assists"] = round(ast, 1) if ast >= 0 and ast < 500 else round(ast / games, 1)
    to = _safe_float(data.get("turnovers")) or _safe_float(data.get("turnovers_per_game"))
    if to is not None:
        out["turnovers"] = round(to, 1) if to >= 0 and to < 500 else round(to / games, 1)
    return out


# --- American Football (NFL) ---

def extract_football_team_stats(raw: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract normalized stats from API-Sports American Football statistics response.
    Returns only keys that exist; per-game when totals provided.
    """
    out: Dict[str, Any] = {}
    if not raw or not isinstance(raw, dict):
        return out
    resp = raw.get("response")
    if isinstance(resp, list) and resp:
        data = resp[0] if isinstance(resp[0], dict) else {}
    elif isinstance(resp, dict):
        data = resp
    else:
        data = raw
    if not data:
        return out
    games = _safe_int(data.get("games")) or _safe_int(data.get("games_played")) or 1
    if games <= 0:
        games = 1
    pts = _safe_float(data.get("points")) or _safe_float(data.get("points_for"))
    if pts is not None:
        out["points_for"] = round(pts / games, 1)
    pts_against = _safe_float(data.get("points_against"))
    if pts_against is not None:
        out["points_against"] = round(pts_against / games, 1)
    total_yards = _safe_float(data.get("total_yards")) or _safe_float(data.get("yards_total"))
    if total_yards is not None:
        out["total_yards"] = round(total_yards / games, 1)
    pass_yards = _safe_float(data.get("pass_yards")) or _safe_float(data.get("passing_yards"))
    if pass_yards is not None:
        out["pass_yards"] = round(pass_yards / games, 1)
    rush_yards = _safe_float(data.get("rush_yards")) or _safe_float(data.get("rushing_yards"))
    if rush_yards is not None:
        out["rush_yards"] = round(rush_yards / games, 1)
    to = _safe_float(data.get("turnovers")) or _safe_int(data.get("turnovers"))
    if to is not None:
        out["turnovers"] = round(to / games, 1) if to >= 0 and to < 100 else round(to, 1)
    third_down = _pct_to_100(data.get("third_down_pct")) or _pct_to_100(data.get("third_downs_pct"))
    if third_down is not None:
        out["third_down_pct"] = third_down
    return out


# --- Hockey (NHL) ---

def extract_hockey_team_stats(raw: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract normalized stats from API-Sports hockey statistics response.
    Returns only keys that exist; per-game when totals provided.
    """
    out: Dict[str, Any] = {}
    if not raw or not isinstance(raw, dict):
        return out
    resp = raw.get("response")
    if isinstance(resp, list) and resp:
        data = resp[0] if isinstance(resp[0], dict) else {}
    elif isinstance(resp, dict):
        data = resp
    else:
        data = raw
    if not data:
        return out
    games = _safe_int(data.get("games")) or _safe_int(data.get("games_played")) or 1
    if games <= 0:
        games = 1
    gf = _safe_float(data.get("goals_for")) or _safe_float(data.get("goals"))
    if gf is not None:
        out["goals_for"] = round(gf / games, 2) if gf >= 0 and gf < 500 else round(gf, 2)
    ga = _safe_float(data.get("goals_against"))
    if ga is not None:
        out["goals_against"] = round(ga / games, 2) if ga >= 0 and ga < 500 else round(ga, 2)
    sf = _safe_float(data.get("shots_for")) or _safe_float(data.get("shots"))
    if sf is not None:
        out["shots_for"] = round(sf / games, 1) if sf >= 0 and sf < 5000 else round(sf, 1)
    sa = _safe_float(data.get("shots_against"))
    if sa is not None:
        out["shots_against"] = round(sa / games, 1) if sa >= 0 and sa < 5000 else round(sa, 1)
    pp = _pct_to_100(data.get("power_play_pct")) or _pct_to_100(data.get("power_play_percentage"))
    if pp is not None:
        out["power_play_pct"] = pp
    pk = _pct_to_100(data.get("penalty_kill_pct")) or _pct_to_100(data.get("penalty_kill_percentage"))
    if pk is not None:
        out["penalty_kill_pct"] = pk
    save_pct = _pct_to_100(data.get("save_pct")) or _pct_to_100(data.get("save_percentage"))
    if save_pct is not None:
        out["save_pct"] = save_pct
    return out


# --- Baseball (MLB) ---

def extract_baseball_team_stats(raw: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract normalized stats from API-Sports baseball statistics response.
    Returns only keys that exist; per-game for runs when totals provided.
    """
    out: Dict[str, Any] = {}
    if not raw or not isinstance(raw, dict):
        return out
    resp = raw.get("response")
    if isinstance(resp, list) and resp:
        data = resp[0] if isinstance(resp[0], dict) else {}
    elif isinstance(resp, dict):
        data = resp
    else:
        data = raw
    if not data:
        return out
    games = _safe_int(data.get("games")) or _safe_int(data.get("games_played")) or 1
    if games <= 0:
        games = 1
    runs = _safe_float(data.get("runs")) or _safe_float(data.get("runs_for"))
    if runs is not None:
        out["runs_for"] = round(runs / games, 2) if runs >= 0 and runs < 2000 else round(runs, 2)
    ra = _safe_float(data.get("runs_against"))
    if ra is not None:
        out["runs_against"] = round(ra / games, 2) if ra >= 0 and ra < 2000 else round(ra, 2)
    avg = _pct_to_100(data.get("avg")) or _safe_float(data.get("batting_average"))
    if avg is not None:
        out["avg"] = round(avg, 3) if avg <= 1 else round(avg / 100, 3)
    obp = _pct_to_100(data.get("obp")) or _safe_float(data.get("on_base_pct"))
    if obp is not None:
        out["obp"] = round(obp / 100, 3) if obp > 1 else round(obp, 3)
    era = _safe_float(data.get("era"))
    if era is not None:
        out["era"] = round(era, 2)
    whip = _safe_float(data.get("whip"))
    if whip is not None:
        out["whip"] = round(whip, 2)
    hr = _safe_int(data.get("hr")) or _safe_int(data.get("home_runs"))
    if hr is not None:
        out["hr"] = hr
    return out


# --- Soccer ---

def extract_soccer_team_stats(raw: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract normalized stats from API-Sports football (soccer) team statistics response.
    Returns only keys that exist; per-game when totals provided.
    """
    out: Dict[str, Any] = {}
    if not raw or not isinstance(raw, dict):
        return out
    resp = raw.get("response")
    if isinstance(resp, dict):
        data = resp
    elif isinstance(resp, list) and resp and isinstance(resp[0], dict):
        data = resp[0]
    else:
        data = raw
    if not data:
        return out
    # API-Football team statistics often has "fixtures" and "goals"
    fixtures = data.get("fixtures") or {}
    if isinstance(fixtures, dict):
        played = _safe_int(fixtures.get("played")) or _safe_int(fixtures.get("games_played")) or 1
    else:
        played = 1
    if played <= 0:
        played = 1
    goals = data.get("goals") or {}
    if isinstance(goals, dict):
        gf = _safe_int(goals.get("for")) or _safe_int(goals.get("total")) or _safe_float(goals.get("for"))
        ga = _safe_int(goals.get("against")) or _safe_float(goals.get("against"))
    else:
        gf = ga = None
    if gf is not None:
        out["goals_for"] = round(float(gf) / played, 2)
    if ga is not None:
        out["goals_against"] = round(float(ga) / played, 2)
    # Optional
    sot = data.get("shots_on_goal") or data.get("shots_on_target")
    if sot is not None:
        s = _safe_float(sot)
        if s is not None:
            out["shots_on_target"] = round(s / played, 1) if s >= 0 and s < 1000 else round(s, 1)
    poss = data.get("possession") or data.get("possession_pct")
    if poss is not None:
        p = _pct_to_100(poss)
        if p is not None:
            out["possession"] = p
    clean = _safe_int(data.get("clean_sheet")) or _safe_int(data.get("clean_sheets"))
    if clean is not None:
        out["clean_sheets"] = clean
    return out
