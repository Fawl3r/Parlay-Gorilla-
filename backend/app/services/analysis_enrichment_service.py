"""
Analysis enrichment from API-Sports: standings, team stats, form, injuries (budget-safe).

Single pipeline for all sports; uses capability map and cached datasets.
Timebox 5s; on failure returns None or partial payload with data_quality notes.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import Game
from app.schemas.enrichment import (
    DataQualitySchema,
    EnrichmentIdsSchema,
    EnrichmentPayloadSchema,
    InjuryStatusCount,
    KeyTeamStatRow,
    TeamEnrichmentSchema,
)
from app.services.apisports.capabilities import get_capability, supports_form, supports_injuries
from app.services.apisports.client import get_apisports_client
from app.services.apisports.enrichment_cache import get_cached, get_cached_with_timestamp, set_cached
from app.services.apisports.league_resolver import get_league_id_for_sport, is_enrichment_supported_for_sport
from app.services.apisports.stats_merge import merge_stats
from app.services.apisports.stat_extractors import (
    extract_baseball_team_stats,
    extract_basketball_team_stats,
    extract_football_team_stats,
    extract_hockey_team_stats,
    extract_key_stats_baseball,
    extract_key_stats_basketball,
    extract_key_stats_football,
    extract_key_stats_hockey,
    extract_soccer_team_stats,
    format_display_value,
)
from app.services.apisports.teams_index_service import get_teams_index, normalize_team_name, resolve_team_id
from app.services.apisports.quota_manager import get_quota_manager
from app.services.apisports.season_resolver import get_season_for_sport_at_date, get_season_int_for_sport_at_date
from app.services.sports_config import get_sport_config

logger = logging.getLogger(__name__)

# Key order and labels for key_team_stats table (parity across sports; profile per sport in capabilities)
STAT_LABELS: Dict[str, str] = {
    "points_for": "PF", "points_against": "PA", "wins": "W", "losses": "L",
    "fg_pct": "FG%", "three_pct": "3P%", "ft_pct": "FT%", "rebounds": "REB",
    "assists": "AST", "turnovers": "TO", "goals_for": "GF", "goals_against": "GA",
    "runs_for": "R", "runs_against": "RA", "total_yards": "YDS", "pass_yards": "PASS", "rush_yards": "RUSH",
}
STAT_KEYS_ORDER: List[str] = [
    "points_for", "points_against", "wins", "losses", "fg_pct", "three_pct", "ft_pct",
    "rebounds", "assists", "turnovers", "goals_for", "goals_against", "runs_for", "runs_against",
    "total_yards", "pass_yards", "rush_yards",
]

ENRICHMENT_TIMEOUT_SECONDS = 5.0
BUDGET_RESERVE = 10
FORM_DAYS_BACK = 14
FORM_LAST_N = 5

# User-safe data_quality.notes (no raw errors or stack traces)
NOTE_PROVIDER_NOT_CONFIGURED = "Stats provider not configured for this sport."
NOTE_BUDGET_LOW = "API-Sports daily budget low; advanced stats temporarily disabled."
NOTE_TEAM_MAPPING_FAILED = "Advanced stats unavailable (team mapping failed)."
NOTE_PROVIDER_UNAVAILABLE = "Advanced stats temporarily unavailable."
NOTE_STANDINGS_UNAVAILABLE = "Standings not available for this league/season."


async def _fetch_on_demand_team_stats(
    client: Any,
    quota: Any,
    sport_slug: str,
    sport_key: str,
    league_id: int,
    season_str: str,
    season_int: int,
    team_id: int,
) -> Tuple[Dict[str, Any], Optional[str]]:
    """
    Fetch team season stats on-demand (cache 12h). Budget check before call.
    Returns (normalized stats dict, cached_at_iso or None). Empty dict + None if unavailable.
    """
    cached, cached_at = await get_cached_with_timestamp(
        "team_stats", sport_key, league_id, season_str, str(team_id)
    )
    if cached is not None and isinstance(cached, dict):
        return (cached, cached_at)
    if await quota.remaining_async(sport_key) < BUDGET_RESERVE:
        try:
            from app.services.apisports.telemetry_helpers import inc_call_blocked_budget
            inc_call_blocked_budget("team_stats", sport_key)
        except Exception:
            pass
        return ({}, None)
    raw = await client.get_team_stats(league_id, season_str, team_id, sport_slug)
    slug = (sport_slug or "").lower().strip()
    if slug in ("nba", "wnba"):
        out = extract_basketball_team_stats(raw) if raw else {}
    elif slug == "nfl":
        out = extract_football_team_stats(raw) if raw else {}
    elif slug == "nhl":
        out = extract_hockey_team_stats(raw) if raw else {}
    elif slug == "mlb":
        out = extract_baseball_team_stats(raw) if raw else {}
    elif slug in ("epl", "mls", "laliga", "ucl"):
        out = extract_soccer_team_stats(raw) if raw else {}
    else:
        out = {}
    if out:
        await set_cached("team_stats", sport_key, league_id, season_str, out, str(team_id))
        now_iso = datetime.now(timezone.utc).isoformat()
        return (out, now_iso)
    return (out, None)


def _parse_standings_response(response: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not response or not isinstance(response, dict):
        return []
    resp_list = response.get("response")
    if not isinstance(resp_list, list) or not resp_list:
        return []
    entries: List[Dict[str, Any]] = []
    for item in resp_list:
        if not isinstance(item, dict):
            continue
        league = item.get("league") if isinstance(item.get("league"), dict) else {}
        standings = league.get("standings") if isinstance(league, dict) else None
        if isinstance(standings, list):
            for group in standings:
                if isinstance(group, list):
                    entries.extend(group)
                elif isinstance(group, dict):
                    entries.append(group)
    return entries


def _match_team_in_standings(team_name: str, entries: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    norm = normalize_team_name(team_name)
    if not norm:
        return None
    for entry in entries:
        team_obj = entry.get("team") if isinstance(entry.get("team"), dict) else {}
        entry_name = (team_obj.get("name") or entry.get("name") or "").strip()
        if not entry_name:
            continue
        if normalize_team_name(entry_name) == norm:
            return entry
        if norm in normalize_team_name(entry_name) or normalize_team_name(entry_name) in norm:
            return entry
    return None


def _team_stats_from_standing(entry: Dict[str, Any], sport_slug: str) -> Dict[str, Any]:
    """Extract sport-appropriate stats from standings entry via per-sport extractors."""
    if not entry or not isinstance(entry, dict):
        return {}
    if sport_slug in ("nba", "wnba"):
        return extract_key_stats_basketball(entry)
    if sport_slug == "nfl":
        return extract_key_stats_football(entry)
    if sport_slug == "nhl":
        return extract_key_stats_hockey(entry)
    if sport_slug == "mlb":
        return extract_key_stats_baseball(entry)
    # Fallback: goals/record for other leagues (e.g. soccer)
    out: Dict[str, Any] = {}
    goals = entry.get("goalsFor") or entry.get("goals_for")
    if goals is not None:
        try:
            out["points_for"] = int(goals)
        except (TypeError, ValueError):
            pass
    goals_against = entry.get("goalsAgainst") or entry.get("goals_against")
    if goals_against is not None:
        try:
            out["points_against"] = int(goals_against)
        except (TypeError, ValueError):
            pass
    all_ = entry.get("all") if isinstance(entry.get("all"), dict) else entry.get("games")
    if isinstance(all_, dict):
        w = all_.get("win")
        l = all_.get("lose")
        if w is not None:
            out["wins"] = int(w)
        if l is not None:
            out["losses"] = int(l)
    return out


def _build_key_team_stats(
    home_enr: TeamEnrichmentSchema,
    away_enr: TeamEnrichmentSchema,
    sport_slug: str,
) -> List[KeyTeamStatRow]:
    """Build key_team_stats table rows from home/away team_stats; order/labels from capability key_stats_profile."""
    all_keys = set()
    if home_enr.team_stats:
        all_keys.update(home_enr.team_stats.keys())
    if away_enr.team_stats:
        all_keys.update(away_enr.team_stats.keys())
    cap = get_capability(sport_slug)
    profile = getattr(cap, "key_stats_profile", None) or []
    order_from_profile = [k for k, _ in profile if k in all_keys]
    order_rest = [k for k in STAT_KEYS_ORDER if k in all_keys and k not in order_from_profile]
    order_rest += sorted(all_keys - set(order_from_profile) - set(order_rest))
    ordered = order_from_profile + order_rest
    label_map = dict(profile) if profile else STAT_LABELS
    rows: List[KeyTeamStatRow] = []
    for k in ordered:
        label = label_map.get(k, STAT_LABELS.get(k, k.replace("_", " ").title()))
        hv = home_enr.team_stats.get(k) if home_enr.team_stats else None
        av = away_enr.team_stats.get(k) if away_enr.team_stats else None
        if hv is not None or av is not None:
            rows.append(KeyTeamStatRow(
                key=k,
                label=label,
                home_value=format_display_value(k, hv) if hv is not None else None,
                away_value=format_display_value(k, av) if av is not None else None,
            ))
    return rows


def _parse_injuries_to_counts(response: Optional[Dict[str, Any]], team_id: Optional[int]) -> List[InjuryStatusCount]:
    """Aggregate injuries to counts by status (no player names)."""
    counts: Dict[str, int] = {}
    if not response or not isinstance(response, dict):
        return []
    resp_list = response.get("response")
    if not isinstance(resp_list, list):
        return []
    for item in resp_list:
        if not isinstance(item, dict):
            continue
        if team_id is not None:
            p_team = (item.get("team") or {}) if isinstance(item.get("team"), dict) else {}
            tid = p_team.get("id") if isinstance(p_team, dict) else None
            if tid != team_id:
                continue
        status = (item.get("player") or {}).get("injured") if isinstance(item.get("player"), dict) else item.get("injured")
        if not status:
            status = item.get("status") or "unknown"
        status = str(status).lower().strip() or "unknown"
        counts[status] = counts.get(status, 0) + 1
    return [InjuryStatusCount(status=k, count=v) for k, v in sorted(counts.items()) if v > 0]


def _parse_games_to_form(games_response: Optional[Dict[str, Any]], team_id: int) -> List[str]:
    """From API-Sports games response, compute last N results (W/L) for team_id. Most recent first."""
    if not games_response or not isinstance(games_response, dict):
        return []
    resp = games_response.get("response")
    if not isinstance(resp, list):
        return []
    results: List[Tuple[datetime, str]] = []
    for g in resp:
        if not isinstance(g, dict):
            continue
        teams = g.get("teams") or g.get("teams") if isinstance(g.get("teams"), dict) else {}
        if not isinstance(teams, dict):
            home = g.get("home_team") or g.get("home")
            away = g.get("away_team") or g.get("away")
            if isinstance(home, dict):
                home_id = home.get("id")
            else:
                home_id = home
            if isinstance(away, dict):
                away_id = away.get("id")
            else:
                away_id = away
        else:
            home = teams.get("home") or teams.get("home_team")
            away = teams.get("away") or teams.get("away_team")
            home_id = home.get("id") if isinstance(home, dict) else None
            away_id = away.get("id") if isinstance(away, dict) else None
        if home_id != team_id and away_id != team_id:
            continue
        score = g.get("scores") or g.get("score") or {}
        if isinstance(score, dict):
            home_goals = score.get("home") or (score.get("fulltime") or {}).get("home")
            away_goals = score.get("away") or (score.get("fulltime") or {}).get("away")
        else:
            home_goals = away_goals = None
        if home_goals is None or away_goals is None:
            continue
        dt_str = (g.get("date") or g.get("fixture") or {}) if isinstance(g.get("fixture"), dict) else g.get("date")
        if isinstance(g.get("fixture"), dict):
            dt_str = g["fixture"].get("date")
        try:
            from dateutil import parser as date_parser
            dt = date_parser.parse(dt_str) if dt_str else datetime.now(timezone.utc)
        except Exception:
            dt = datetime.now(timezone.utc)
        is_home = home_id == team_id
        won = (is_home and home_goals > away_goals) or (not is_home and away_goals > home_goals)
        results.append((dt, "W" if won else "L"))
    results.sort(key=lambda x: x[0], reverse=True)
    return [r[1] for r in results[:FORM_LAST_N]]


async def build_enrichment_for_game(
    db: AsyncSession,
    game: Game,
    sport_slug: str,
    *,
    timeout_seconds: float = ENRICHMENT_TIMEOUT_SECONDS,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Build full enrichment payload: standings, team stats, form, injuries.
    Returns (payload, None) on success or partial; (None, reason) when unavailable.
    """
    if not game or not sport_slug or not is_enrichment_supported_for_sport(sport_slug):
        return (None, NOTE_PROVIDER_NOT_CONFIGURED)
    league_id = get_league_id_for_sport(sport_slug)
    if league_id is None:
        return (None, NOTE_PROVIDER_NOT_CONFIGURED)
    start = time.perf_counter()
    try:
        sport_config = get_sport_config(sport_slug)
        sport_key = sport_config.odds_key
        game_time = getattr(game, "start_time", None) or datetime.now(timezone.utc)
        season_str = get_season_for_sport_at_date(sport_key, game_time)
        season_int = get_season_int_for_sport_at_date(sport_key, game_time)
        cap = get_capability(sport_slug)
        quota = get_quota_manager()
        remaining = await quota.remaining_async(sport_key)
        if remaining < BUDGET_RESERVE:
            try:
                from app.services.apisports.telemetry_helpers import inc_call_blocked_budget
                inc_call_blocked_budget(dataset="teams_index", sport=sport_key)
            except Exception:
                pass
            return (None, NOTE_BUDGET_LOW)
        client = get_apisports_client()
        if not client.is_configured():
            return (
                _make_partial_payload(
                    sport_config, sport_slug, season_str, game,
                    data_quality_notes=[NOTE_PROVIDER_NOT_CONFIGURED],
                    build_time_ms=(time.perf_counter() - start) * 1000,
                ),
                None,
            )

        async def _build() -> Optional[Dict[str, Any]]:
            from app.services.apisports.telemetry_helpers import (
                inc_cache_miss,
                inc_call_made,
            )

            async def _budget_ok() -> bool:
                return await quota.remaining_async(sport_key) >= BUDGET_RESERVE

            source_timestamps: Dict[str, Optional[str]] = {}

            # 1) Teams index (cached 24h); skip provider call if budget low
            teams_index, teams_ts = await get_cached_with_timestamp("teams", sport_key, league_id, season_str)
            if teams_index is None and await _budget_ok():
                teams_index = await get_teams_index(client, sport_key, league_id, season_str, sport_slug)
                if teams_index is not None:
                    teams_ts = datetime.now(timezone.utc).isoformat()
            if teams_index is None:
                teams_index = {}
            if teams_ts:
                source_timestamps["teams_index"] = teams_ts
            home_id = resolve_team_id(teams_index, game.home_team or "")
            away_id = resolve_team_id(teams_index, game.away_team or "")
            if home_id is None or away_id is None:
                try:
                    from app.services.apisports.telemetry_helpers import inc_enrichment_partial
                    inc_enrichment_partial("team_map_failed")
                except Exception:
                    pass

            # 2) Standings (cached 6h); skip provider call if budget low
            standings_raw, standings_ts = await get_cached_with_timestamp(
                "standings", sport_key, league_id, season_str
            )
            if standings_raw is None and await _budget_ok():
                inc_cache_miss("standings")
                standings_raw = await client.get_standings(league_id=league_id, season=season_int, sport=sport_key)
                if standings_raw is not None:
                    await set_cached("standings", sport_key, league_id, season_str, standings_raw)
                    standings_ts = datetime.now(timezone.utc).isoformat()
                inc_call_made("standings", sport_slug)
            if standings_ts:
                source_timestamps["standings"] = standings_ts
            entries = _parse_standings_response(standings_raw) if standings_raw else []
            home_entry = _match_team_in_standings(game.home_team or "", entries)
            away_entry = _match_team_in_standings(game.away_team or "", entries)

            home_enr = _team_enrichment_from_standing(game.home_team or "", home_entry, sport_slug, home_id)
            away_enr = _team_enrichment_from_standing(game.away_team or "", away_entry, sport_slug, away_id)

            # 2b) On-demand team stats (cached 12h); primary=raw, fallback=standings; merge_stats fills missing only
            team_stats_ts: Optional[str] = None
            cap = get_capability(sport_slug)
            if cap.team_stats and league_id is not None:
                if home_id is not None:
                    on_demand_home, ts_home = await _fetch_on_demand_team_stats(
                        client, quota, sport_slug, sport_key, league_id, season_str, season_int, home_id
                    )
                    home_enr = home_enr.model_copy(
                        update={"team_stats": merge_stats(on_demand_home, home_enr.team_stats)}
                    )
                    if ts_home and (team_stats_ts is None or ts_home > team_stats_ts):
                        team_stats_ts = ts_home
                if away_id is not None:
                    on_demand_away, ts_away = await _fetch_on_demand_team_stats(
                        client, quota, sport_slug, sport_key, league_id, season_str, season_int, away_id
                    )
                    away_enr = away_enr.model_copy(
                        update={"team_stats": merge_stats(on_demand_away, away_enr.team_stats)}
                    )
                    if ts_away and (team_stats_ts is None or ts_away > team_stats_ts):
                        team_stats_ts = ts_away
                if team_stats_ts:
                    source_timestamps["team_stats"] = team_stats_ts

            # 3) Form: fetch games for last N days (each day cached 2h), merge and compute W/L per team; skip call if budget low
            form_ts: Optional[str] = None
            if supports_form(sport_slug):
                form_by_team: Dict[int, List[str]] = {}
                today = datetime.now(timezone.utc).date()
                for d in range(FORM_DAYS_BACK):
                    day = today - timedelta(days=d)
                    date_str = day.strftime("%Y-%m-%d")
                    day_cached, day_ts = await get_cached_with_timestamp(
                        "form", sport_key, league_id, season_str, date_str
                    )
                    if day_cached is None and await _budget_ok():
                        inc_cache_miss("form")
                        day_raw = await client.get_games(league_id=league_id, season=season_str, date=date_str, sport=sport_key)
                        if day_raw:
                            await set_cached("form", sport_key, league_id, season_str, day_raw, date_str)
                            day_ts = datetime.now(timezone.utc).isoformat()
                        inc_call_made("form", sport_slug)
                        day_cached = day_raw
                    if day_ts and (form_ts is None or day_ts > form_ts):
                        form_ts = day_ts
                    if day_cached and isinstance(day_cached, dict):
                        resp = day_cached.get("response")
                        if isinstance(resp, list):
                            for gm in resp:
                                if not isinstance(gm, dict):
                                    continue
                                teams = gm.get("teams") or {}
                                h = (teams.get("home") or {}).get("id") if isinstance(teams.get("home"), dict) else gm.get("home_team_id")
                                a = (teams.get("away") or {}).get("id") if isinstance(teams.get("away"), dict) else gm.get("away_team_id")
                                if not h or not a:
                                    continue
                                for tid in (h, a):
                                    if tid not in form_by_team:
                                        form_by_team[tid] = []
                                    if len(form_by_team[tid]) < FORM_LAST_N:
                                        score = gm.get("scores") or gm.get("score") or {}
                                        hg = score.get("home") or (isinstance(score.get("fulltime"), dict) and score["fulltime"].get("home"))
                                        ag = score.get("away") or (isinstance(score.get("fulltime"), dict) and score["fulltime"].get("away"))
                                        if hg is not None and ag is not None:
                                            form_by_team[tid].append("W" if (tid == h and hg > ag) or (tid == a and ag > hg) else "L")
                if home_id and home_id in form_by_team:
                    home_enr.recent_form = form_by_team[home_id][:FORM_LAST_N]
                if away_id and away_id in form_by_team:
                    away_enr.recent_form = form_by_team[away_id][:FORM_LAST_N]
                if form_ts:
                    source_timestamps["form"] = form_ts

            # 4) Injuries (cached 60m) — counts only; skip provider call if budget low
            has_injuries = False
            if supports_injuries(sport_slug):
                inj_raw, injuries_ts = await get_cached_with_timestamp(
                    "injuries", sport_key, league_id, season_str
                )
                if inj_raw is None and await _budget_ok():
                    inc_cache_miss("injuries")
                    inj_raw = await client.get_injuries(league_id=league_id, season=season_int, sport=sport_key)
                    if inj_raw is not None:
                        await set_cached("injuries", sport_key, league_id, season_str, inj_raw)
                        injuries_ts = datetime.now(timezone.utc).isoformat()
                    inc_call_made("injuries", sport_slug)
                if injuries_ts:
                    source_timestamps["injuries"] = injuries_ts
                if inj_raw:
                    home_enr.injuries_summary = _parse_injuries_to_counts(inj_raw, home_id)
                    away_enr.injuries_summary = _parse_injuries_to_counts(inj_raw, away_id)
                    has_injuries = bool(home_enr.injuries_summary or away_enr.injuries_summary)

            data_quality_notes: List[str] = []
            if not entries:
                data_quality_notes.append(NOTE_STANDINGS_UNAVAILABLE)
            if (home_id is None and (game.home_team or "").strip()) or (away_id is None and (game.away_team or "").strip()):
                data_quality_notes.append(NOTE_TEAM_MAPPING_FAILED)
            dq = DataQualitySchema(
                has_standings=len(entries) > 0,
                has_team_stats=bool(home_enr.team_stats or away_enr.team_stats),
                has_form=bool(home_enr.recent_form or away_enr.recent_form),
                has_injuries=has_injuries,
                notes=data_quality_notes,
                source_timestamps=source_timestamps,
            )
            ids = EnrichmentIdsSchema(
                apisports_league_id=league_id,
                season=season_str,
                home_team_id=home_id,
                away_team_id=away_id,
            )
            key_team_stats = _build_key_team_stats(home_enr, away_enr, sport_slug)
            payload = EnrichmentPayloadSchema(
                sport=sport_slug,
                league=sport_config.display_name,
                season=season_str,
                league_id=league_id,
                home_team=home_enr,
                away_team=away_enr,
                key_team_stats=key_team_stats,
                data_quality=dq,
                ids=ids,
                as_of=datetime.now(timezone.utc),
            )
            build_time_ms = (time.perf_counter() - start) * 1000
            try:
                from app.services.apisports.telemetry_helpers import inc_enrichment_build_time_ms
                inc_enrichment_build_time_ms(build_time_ms)
            except Exception:
                pass
            return _enrichment_to_dict(payload, build_time_ms)
        result = await asyncio.wait_for(_build(), timeout=timeout_seconds)
        return (result, None)
    except asyncio.TimeoutError:
        logger.warning("Analysis enrichment timed out for game %s", getattr(game, "id", ""))
        try:
            from app.services.apisports.telemetry_helpers import inc_enrichment_partial
            inc_enrichment_partial("timeout")
        except Exception:
            pass
        return (None, NOTE_PROVIDER_UNAVAILABLE)
    except Exception as e:
        logger.warning("Analysis enrichment failed: %s", e, exc_info=False)
        try:
            from app.services.apisports.telemetry_helpers import inc_enrichment_partial
            inc_enrichment_partial("provider_error")
        except Exception:
            pass
        return (None, NOTE_PROVIDER_UNAVAILABLE)


def _team_enrichment_from_standing(
    team_name: str,
    entry: Optional[Dict[str, Any]],
    sport_slug: str,
    apisports_team_id: Optional[int],
) -> TeamEnrichmentSchema:
    rank = None
    record = None
    team_id = apisports_team_id
    team_stats: Dict[str, Any] = {}
    if entry:
        team_obj = entry.get("team")
        if isinstance(team_obj, dict):
            team_id = team_id or team_obj.get("id")
        r = entry.get("position") or entry.get("rank")
        if r is not None:
            rank = int(r) if isinstance(r, (int, float)) else None
        wins = entry.get("games", {}).get("win") if isinstance(entry.get("games"), dict) else entry.get("win")
        losses = entry.get("games", {}).get("lose") if isinstance(entry.get("games"), dict) else entry.get("lose")
        if wins is not None and losses is not None:
            record = f"{wins}-{losses}"
        elif isinstance(entry.get("all"), dict):
            all_ = entry["all"]
            record = f"{all_.get('win', '')}-{all_.get('lose', '')}".strip("-") or None
        team_stats = _team_stats_from_standing(entry, sport_slug)
    return TeamEnrichmentSchema(
        name=team_name or "",
        apisports_team_id=team_id,
        record=record,
        standings_rank=rank,
        team_stats=team_stats,
        recent_form=[],
        injuries_summary=[],
    )


def _make_partial_payload(
    sport_config: Any,
    sport_slug: str,
    season_str: str,
    game: Game,
    data_quality_notes: List[str],
    build_time_ms: float = 0,
    source_timestamps: Optional[Dict[str, Optional[str]]] = None,
) -> Dict[str, Any]:
    home = TeamEnrichmentSchema(name=game.home_team or "")
    away = TeamEnrichmentSchema(name=game.away_team or "")
    dq = DataQualitySchema(
        has_standings=False,
        has_team_stats=False,
        has_form=False,
        has_injuries=False,
        notes=data_quality_notes,
        source_timestamps=source_timestamps or {},
    )
    payload = EnrichmentPayloadSchema(
        sport=sport_slug,
        league=sport_config.display_name,
        season=season_str,
        league_id=None,
        home_team=home,
        away_team=away,
        key_team_stats=[],
        data_quality=dq,
        as_of=datetime.now(timezone.utc),
    )
    return _enrichment_to_dict(payload, build_time_ms)


def _enrichment_to_dict(payload: EnrichmentPayloadSchema, build_time_ms: float = 0) -> Dict[str, Any]:
    def team_to_dict(t: TeamEnrichmentSchema) -> Dict[str, Any]:
        d: Dict[str, Any] = {"name": t.name}
        if t.apisports_team_id is not None:
            d["apisports_team_id"] = t.apisports_team_id
        if t.record is not None:
            d["record"] = t.record
        if t.standings_rank is not None:
            d["standings_rank"] = t.standings_rank
        if t.recent_form:
            d["recent_form"] = t.recent_form
        if t.team_stats:
            d["team_stats"] = t.team_stats
        if t.injuries_summary:
            d["injuries_summary"] = [{"status": s.status, "count": s.count} for s in t.injuries_summary]
        return d

    out = {
        "sport": payload.sport,
        "league": payload.league,
        "season": payload.season,
        "league_id": payload.league_id,
        "home_team": team_to_dict(payload.home_team),
        "away_team": team_to_dict(payload.away_team),
        "key_team_stats": [
            {"key": r.key, "label": r.label, "home_value": r.home_value, "away_value": r.away_value}
            for r in payload.key_team_stats
        ],
        "data_quality": {
            "has_standings": payload.data_quality.has_standings,
            "has_team_stats": payload.data_quality.has_team_stats,
            "has_form": payload.data_quality.has_form,
            "has_injuries": payload.data_quality.has_injuries,
            "notes": payload.data_quality.notes,
            "source_timestamps": payload.data_quality.source_timestamps or {},
        },
    }
    if payload.as_of:
        out["as_of"] = payload.as_of.isoformat()
    if payload.ids:
        out["ids"] = {
            "apisports_league_id": payload.ids.apisports_league_id,
            "season": payload.ids.season,
            "home_team_id": payload.ids.home_team_id,
            "away_team_id": payload.ids.away_team_id,
        }
    if build_time_ms > 0:
        try:
            from app.core import telemetry
            telemetry.inc("enrichment_build_time_ms", n=int(build_time_ms))
        except Exception:
            pass
    return out


async def fetch_enrichment_for_game(
    db: AsyncSession,
    game: Game,
    sport_slug: str,
    *,
    timeout_seconds: float = ENRICHMENT_TIMEOUT_SECONDS,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Fetch API-Sports enrichment for a game. Returns (enrichment, unavailable_reason)."""
    return await build_enrichment_for_game(db, game, sport_slug, timeout_seconds=timeout_seconds)
