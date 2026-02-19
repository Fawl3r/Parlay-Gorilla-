"""
API-Sports team-stats integration contract tests.

Verifies live provider: params, response shape, and stat_extractors compatibility.
Skipped unless APISPORTS_API_KEY (or API_SPORTS_API_KEY) is set.
Do not run in normal CI; run explicitly with: pytest tests/integration -m integration
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

import pytest

from app.core.config import settings
from app.services.apisports.client import get_apisports_client
from app.services.apisports.endpoints import get_team_stats_endpoint
from app.services.apisports.league_resolver import get_league_id_for_sport
from app.services.apisports.season_resolver import get_season_for_sport_at_date
from app.services.apisports.stat_extractors import (
    extract_baseball_team_stats,
    extract_basketball_team_stats,
    extract_football_team_stats,
    extract_hockey_team_stats,
    extract_soccer_team_stats,
)

# Rate-limit friendliness: small delay between provider calls
INTEGRATION_CALL_DELAY_SECONDS = 0.25

SPORT_SLUGS = ("nba", "wnba", "nfl", "nhl", "mlb", "epl")
EXTRACTOR_BY_SLUG: Dict[str, Callable[[Optional[Dict[str, Any]]], Dict[str, Any]]] = {
    "nba": extract_basketball_team_stats,
    "wnba": extract_basketball_team_stats,
    "nfl": extract_football_team_stats,
    "nhl": extract_hockey_team_stats,
    "mlb": extract_baseball_team_stats,
    "epl": extract_soccer_team_stats,
}


def _has_api_key() -> bool:
    if os.environ.get("APISPORTS_API_KEY", "").strip():
        return True
    if os.environ.get("API_SPORTS_API_KEY", "").strip():
        return True
    if getattr(settings, "api_sports_api_key", None):
        return True
    return False


def _sport_key_for_teams(sport_slug: str) -> str:
    endpoint = get_team_stats_endpoint(sport_slug)
    if endpoint:
        return endpoint.sport_key
    return (sport_slug or "").lower().strip()


def _truncate_payload(payload: Any, max_len: int = 400) -> str:
    """Truncate for assertion messages."""
    try:
        s = json.dumps(payload) if payload is not None else "null"
        return s[:max_len] + ("..." if len(s) > max_len else "")
    except Exception:
        return str(payload)[:max_len]


def _debug_context(
    sport_slug: str,
    endpoint_path: Optional[str],
    base_url: Optional[str],
    league_id: Optional[int],
    season: Optional[str],
    team_id: Optional[int],
    raw: Any,
) -> str:
    return (
        f" sport_slug={sport_slug} endpoint_path={endpoint_path!r} base_url={base_url!r}"
        f" league_id={league_id} season={season!r} team_id={team_id} payload_trunc={_truncate_payload(raw)}"
    )


def _first_team_id_deterministic(teams_raw: Dict[str, Any]) -> Optional[int]:
    """
    Select team deterministically: filter entries with valid id+name, sort by team_id, pick first.
    Handles response.response as list of {team: {id, name}} or list of {id, name}.
    """
    resp = teams_raw.get("response")
    if not isinstance(resp, list):
        return None
    candidates: List[Tuple[int, str]] = []
    for item in resp:
        if not isinstance(item, dict):
            continue
        team_obj = item.get("team") if isinstance(item.get("team"), dict) else item
        if not isinstance(team_obj, dict):
            continue
        tid = team_obj.get("id")
        name = team_obj.get("name")
        if tid is None or not isinstance(tid, int):
            continue
        name_str = (name or "").strip() if isinstance(name, str) else ""
        if not name_str and name is not None:
            try:
                name_str = str(name).strip()
            except Exception:
                pass
        candidates.append((tid, name_str or ""))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    return candidates[0][0]


@pytest.fixture(scope="module")
def api_key_required():
    """Skip entire module when API key is not set."""
    if not _has_api_key():
        pytest.skip("APISPORTS_API_KEY or API_SPORTS_API_KEY not set; skip integration tests")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_team_stats_contract_nba(api_key_required) -> None:
    await _run_contract("nba")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_team_stats_contract_wnba(api_key_required) -> None:
    await _run_contract("wnba")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_team_stats_contract_nfl(api_key_required) -> None:
    await _run_contract("nfl")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_team_stats_contract_nhl(api_key_required) -> None:
    await _run_contract("nhl")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_team_stats_contract_mlb(api_key_required) -> None:
    await _run_contract("mlb")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_team_stats_contract_epl(api_key_required) -> None:
    await _run_contract("epl")


async def _run_contract(sport_slug: str) -> None:
    league_id = get_league_id_for_sport(sport_slug)
    if league_id is None:
        pytest.skip(f"No league ID configured for {sport_slug} (set APISPORTS_LEAGUE_ID_* env)")

    endpoint = get_team_stats_endpoint(sport_slug)
    if not endpoint:
        pytest.skip(f"No team stats endpoint for {sport_slug}")

    now = datetime.now(timezone.utc)
    season = get_season_for_sport_at_date(sport_slug, now)
    sport_key = _sport_key_for_teams(sport_slug)

    client = get_apisports_client()
    if not client.is_configured():
        pytest.skip("API-Sports client not configured")

    base_url = client._effective_base_url(sport_key)

    teams_raw = await client.get_teams(league_id=league_id, season=season, sport=sport_key)
    await asyncio.sleep(INTEGRATION_CALL_DELAY_SECONDS)

    if not teams_raw or not isinstance(teams_raw, dict):
        pytest.skip(
            f"No teams response for {sport_slug}"
            + _debug_context(sport_slug, endpoint.path, base_url, league_id, season, None, teams_raw)
        )
    if "response" not in teams_raw:
        pytest.skip(
            f"Teams payload missing 'response' key for {sport_slug}"
            + _debug_context(sport_slug, endpoint.path, base_url, league_id, season, None, teams_raw)
        )
    resp_list = teams_raw.get("response")
    if not isinstance(resp_list, list) or not resp_list:
        pytest.skip(
            f"Teams response.response empty or not list for {sport_slug}"
            + _debug_context(sport_slug, endpoint.path, base_url, league_id, season, None, teams_raw)
        )

    team_id = _first_team_id_deterministic(teams_raw)
    if not team_id:
        pytest.skip(
            f"Could not get deterministic team_id from teams response for {sport_slug}"
            + _debug_context(sport_slug, endpoint.path, base_url, league_id, season, None, teams_raw)
        )

    raw = await client.get_team_stats(league_id, season, team_id, sport_slug)
    ctx = _debug_context(sport_slug, endpoint.path, base_url, league_id, season, team_id, raw)

    assert raw is not None, f"get_team_stats returned None for {sport_slug}" + ctx
    assert isinstance(raw, dict), f"get_team_stats did not return dict for {sport_slug}" + ctx
    assert "response" in raw, f"Provider payload missing top-level 'response' for {sport_slug}" + ctx

    response = raw.get("response")
    if isinstance(response, list):
        assert len(response) > 0, f"Provider response.response is empty list for {sport_slug}" + ctx
    elif isinstance(response, dict):
        assert response, f"Provider response.response is empty dict for {sport_slug}" + ctx
    else:
        pytest.fail(f"Provider response is neither list nor dict for {sport_slug}" + ctx)

    extractor = EXTRACTOR_BY_SLUG.get(sport_slug)
    assert extractor is not None, f"No extractor for {sport_slug}" + ctx
    extracted = extractor(raw)
    assert isinstance(extracted, dict), f"Extractor did not return dict for {sport_slug}" + ctx
    assert len(extracted) >= 2, (
        f"Extractor returned fewer than 2 metrics for {sport_slug} (got {list(extracted.keys())})" + ctx
    )


# --- Injuries contract (counts only, no player names) ---


@pytest.mark.integration
@pytest.mark.asyncio
async def test_injuries_contract_counts_only(api_key_required) -> None:
    """
    Call injuries endpoint for one supported sport (nba); assert we can produce
    counts-only summary (status + count, no player names). Skip if endpoint not supported.
    """
    from app.services.analysis_enrichment_service import _parse_injuries_to_counts

    sport_slug = "nba"
    league_id = get_league_id_for_sport(sport_slug)
    if league_id is None:
        pytest.skip(f"No league ID configured for {sport_slug}")

    from app.services.apisports.season_resolver import get_season_int_for_sport_at_date

    now = datetime.now(timezone.utc)
    season_int = get_season_int_for_sport_at_date(sport_slug, now)
    sport_key = "nba"

    client = get_apisports_client()
    if not client.is_configured():
        pytest.skip("API-Sports client not configured")

    await asyncio.sleep(INTEGRATION_CALL_DELAY_SECONDS)
    inj_raw = await client.get_injuries(league_id=league_id, season=season_int, sport=sport_key)

    if inj_raw is None:
        pytest.skip("get_injuries returned None (endpoint may not be supported or plan limit)")
    if not isinstance(inj_raw, dict):
        pytest.skip(f"get_injuries did not return dict: {type(inj_raw).__name__}")
    if "response" not in inj_raw:
        pytest.skip(f"Injuries payload missing 'response' key; trunc={_truncate_payload(inj_raw)}")

    counts = _parse_injuries_to_counts(inj_raw, team_id=None)
    assert isinstance(counts, list), f"Parser did not return list: {type(counts).__name__}"

    for item in counts:
        assert hasattr(item, "status") and hasattr(item, "count"), (
            f"Injury item must have status and count only (counts-only contract); got {item!r}"
        )
        assert isinstance(getattr(item, "status", None), str), "status must be str"
        assert isinstance(getattr(item, "count", None), int), "count must be int"
        # No player name fields
        assert not hasattr(item, "player") or getattr(item, "player", None) is None, (
            "Counts-only: must not expose player names"
        )
        assert not hasattr(item, "name") or getattr(item, "name", None) is None, (
            "Counts-only: must not expose player names"
        )
