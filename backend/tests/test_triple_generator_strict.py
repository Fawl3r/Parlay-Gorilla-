"""
Tests for Triple Parlay confidence-gated behavior (request_mode=TRIPLE).

- Triple success: 3 strong edges → 3 legs, downgraded=false
- Downgrade: 2 strong edges, >=2 eligible → 2 legs, downgraded=true, INSUFFICIENT_STRONG_EDGES
- Hard fail: <2 eligible → 409 NOT_ENOUGH_GAMES with debug_id
- No fallback: Triple path never uses fallback ladder
- Entitlement: mixed sports not broadened when disabled
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock
import uuid

from app.core.parlay_errors import InsufficientCandidatesException
from app.services.entitlements.entitlement_service import ParlaySuggestAccess


def _leg(game_id: str, confidence: float = 65.0):
    return {
        "market_id": f"m_{game_id}",
        "outcome": "home",
        "game": f"Game {game_id}",
        "home_team": "Home",
        "away_team": "Away",
        "market_type": "h2h",
        "odds": "-110",
        "probability": 0.55,
        "confidence": confidence,
        "sport": "NFL",
    }


def _parlay_payload(num_legs: int, mode_returned: str, downgraded: bool = False, **kwargs):
    legs = [_leg(f"g{i}", 65.0 + i) for i in range(num_legs)]
    base = {
        "legs": legs,
        "num_legs": num_legs,
        "parlay_hit_prob": 0.25,
        "risk_profile": "balanced",
        "confidence_scores": [65.0] * num_legs,
        "overall_confidence": 65.0,
        "raw_parlay_hit_prob": 0.25,
        "parlay_ev": 0.0,
        "model_confidence": 0.65,
        "upset_count": 0,
        "model_version": "test",
        "mode_returned": mode_returned,
        "downgraded": downgraded,
    }
    base.update(kwargs)
    return base


@pytest.mark.asyncio
async def test_triple_success_returns_3_legs_downgraded_false(client: AsyncClient, db):
    """When 3 strong edges exist, Triple returns 3 legs and downgraded=false."""
    email = f"triple-ok-{uuid.uuid4()}@test.com"
    await client.post("/api/auth/register", json={"email": email, "password": "Passw0rd!"})
    login = await client.post("/api/auth/login", json={"email": email, "password": "Passw0rd!"})
    token = login.json()["access_token"]

    access = ParlaySuggestAccess(
        allowed=True,
        reason=None,
        features={"mix_sports": True, "max_legs": 20, "player_props": True},
        credits_remaining=10,
    )
    triple_ok = _parlay_payload(3, "TRIPLE", downgraded=False)

    with patch("app.api.routes.parlay.EntitlementService") as MockEntitlement, patch(
        "app.api.routes.parlay.check_parlay_access_with_purchase",
        new_callable=AsyncMock,
        return_value={"can_generate": True, "use_free": True, "error_code": None},
    ), patch("app.api.routes.parlay.ParlayBuilderService") as MockBuilder, patch(
        "app.api.routes.parlay.CacheManager"
    ), patch(
        "app.api.routes.parlay.get_parlay_eligibility",
        new_callable=AsyncMock,
        return_value=MagicMock(eligible_count=10, unique_games=10, exclusion_reasons=[], debug_id="abc", strong_edges=5),
    ):
        MockEntitlement.return_value.get_parlay_suggest_access = AsyncMock(return_value=access)
        mock_builder = MagicMock()
        mock_builder.build_parlay = AsyncMock(return_value=triple_ok)
        MockBuilder.return_value = mock_builder

        resp = await client.post(
            "/api/parlay/suggest",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "num_legs": 3,
                "risk_profile": "balanced",
                "request_mode": "TRIPLE",
                "sports": ["NFL"],
            },
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data.get("num_legs") == 3
    assert len(data.get("legs", [])) == 3
    assert data.get("mode_returned") == "TRIPLE"
    assert data.get("downgraded") is False
    mock_builder.build_parlay.assert_called_once()
    call_kwargs = mock_builder.build_parlay.call_args[1]
    assert call_kwargs.get("request_mode") == "TRIPLE"
    assert call_kwargs.get("num_legs") == 3


@pytest.mark.asyncio
async def test_triple_downgrade_returns_2_legs_downgraded_true(client: AsyncClient, db):
    """When only 2 strong edges but >=2 eligible, returns 2 legs with downgraded=true and INSUFFICIENT_STRONG_EDGES."""
    email = f"triple-downgrade-{uuid.uuid4()}@test.com"
    await client.post("/api/auth/register", json={"email": email, "password": "Passw0rd!"})
    login = await client.post("/api/auth/login", json={"email": email, "password": "Passw0rd!"})
    token = login.json()["access_token"]

    access = ParlaySuggestAccess(
        allowed=True,
        reason=None,
        features={"mix_sports": True, "max_legs": 20, "player_props": True},
        credits_remaining=10,
    )
    downgrade_payload = _parlay_payload(
        2,
        "DOUBLE",
        downgraded=True,
        downgrade_from="TRIPLE",
        downgrade_reason_code="INSUFFICIENT_STRONG_EDGES",
        downgrade_summary={"needed": 3, "have_strong": 2, "have_eligible": 5},
        ui_suggestion={"primary_action": "Reduce to 2 picks (recommended)", "secondary_action": "Expand time window"},
        explain={"short_reason": "Triple requires 3 high-confidence edges. Today we have 2."},
    )

    with patch("app.api.routes.parlay.EntitlementService") as MockEntitlement, patch(
        "app.api.routes.parlay.check_parlay_access_with_purchase",
        new_callable=AsyncMock,
        return_value={"can_generate": True, "use_free": True, "error_code": None},
    ), patch("app.api.routes.parlay.ParlayBuilderService") as MockBuilder, patch(
        "app.api.routes.parlay.CacheManager"
    ), patch(
        "app.api.routes.parlay.get_parlay_eligibility",
        new_callable=AsyncMock,
        return_value=MagicMock(eligible_count=5, unique_games=5, exclusion_reasons=[], debug_id="def", strong_edges=2),
    ):
        MockEntitlement.return_value.get_parlay_suggest_access = AsyncMock(return_value=access)
        mock_builder = MagicMock()
        mock_builder.build_parlay = AsyncMock(return_value=downgrade_payload)
        MockBuilder.return_value = mock_builder

        resp = await client.post(
            "/api/parlay/suggest",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "num_legs": 3,
                "risk_profile": "balanced",
                "request_mode": "TRIPLE",
                "sports": ["NFL"],
            },
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data.get("num_legs") == 2
    assert len(data.get("legs", [])) == 2
    assert data.get("mode_returned") == "DOUBLE"
    assert data.get("downgraded") is True
    assert data.get("downgrade_from") == "TRIPLE"
    assert data.get("downgrade_reason_code") == "INSUFFICIENT_STRONG_EDGES"
    assert data.get("downgrade_summary", {}).get("have_strong") == 2


@pytest.mark.asyncio
async def test_triple_hard_fail_returns_409_not_enough_games(client: AsyncClient, db):
    """When <2 eligible picks, Triple path returns 409 NOT_ENOUGH_GAMES with debug_id."""
    email = f"triple-fail-{uuid.uuid4()}@test.com"
    await client.post("/api/auth/register", json={"email": email, "password": "Passw0rd!"})
    login = await client.post("/api/auth/login", json={"email": email, "password": "Passw0rd!"})
    token = login.json()["access_token"]

    access = ParlaySuggestAccess(
        allowed=True,
        reason=None,
        features={"mix_sports": True, "max_legs": 20, "player_props": True},
        credits_remaining=10,
    )
    eligibility_few = MagicMock(
        eligible_count=1,
        unique_games=1,
        exclusion_reasons=[{"reason": "NO_ODDS", "count": 1}],
        debug_id="xyz123",
        strong_edges=1,
    )

    with patch("app.api.routes.parlay.EntitlementService") as MockEntitlement, patch(
        "app.api.routes.parlay.check_parlay_access_with_purchase",
        new_callable=AsyncMock,
        return_value={"can_generate": True, "use_free": True, "error_code": None},
    ), patch("app.api.routes.parlay.ParlayBuilderService") as MockBuilder, patch(
        "app.api.routes.parlay.CacheManager"
    ), patch(
        "app.api.routes.parlay.get_parlay_eligibility",
        new_callable=AsyncMock,
        return_value=eligibility_few,
    ):
        MockEntitlement.return_value.get_parlay_suggest_access = AsyncMock(return_value=access)
        mock_builder = MagicMock()
        mock_builder.build_parlay = AsyncMock(
            side_effect=InsufficientCandidatesException(
                needed=3,
                have=1,
                message="Not enough eligible games with clean odds right now.",
            )
        )
        MockBuilder.return_value = mock_builder

        resp = await client.post(
            "/api/parlay/suggest",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "num_legs": 3,
                "risk_profile": "balanced",
                "request_mode": "TRIPLE",
                "sports": ["NFL"],
            },
        )

    assert resp.status_code == 409
    data = resp.json()
    assert data.get("code") == "NOT_ENOUGH_GAMES", "Triple hard-fail must return code=NOT_ENOUGH_GAMES"
    assert "debug_id" in data
    assert data.get("debug_id") == "xyz123"
    assert data.get("needed") == 3
    assert data.get("have") == 1
    assert (data.get("meta") or {}).get("strong_edges") == 1


@pytest.mark.asyncio
async def test_triple_no_fallback_ladder_called(client: AsyncClient, db):
    """Triple path calls build_parlay once with request_mode=TRIPLE; no fallback stages (week_expanded, ml_only)."""
    email = f"triple-no-fb-{uuid.uuid4()}@test.com"
    await client.post("/api/auth/register", json={"email": email, "password": "Passw0rd!"})
    login = await client.post("/api/auth/login", json={"email": email, "password": "Passw0rd!"})
    token = login.json()["access_token"]

    access = ParlaySuggestAccess(
        allowed=True,
        reason=None,
        features={"mix_sports": True, "max_legs": 20, "player_props": True},
        credits_remaining=10,
    )
    triple_ok = _parlay_payload(3, "TRIPLE", downgraded=False)

    with patch("app.api.routes.parlay.EntitlementService") as MockEntitlement, patch(
        "app.api.routes.parlay.check_parlay_access_with_purchase",
        new_callable=AsyncMock,
        return_value={"can_generate": True, "use_free": True, "error_code": None},
    ), patch("app.api.routes.parlay.ParlayBuilderService") as MockBuilder, patch(
        "app.api.routes.parlay.CacheManager"
    ), patch(
        "app.api.routes.parlay.get_parlay_eligibility",
        new_callable=AsyncMock,
        return_value=MagicMock(eligible_count=10, unique_games=10, exclusion_reasons=[], debug_id="nofb", strong_edges=5),
    ):
        MockEntitlement.return_value.get_parlay_suggest_access = AsyncMock(return_value=access)
        mock_builder = MagicMock()
        mock_builder.build_parlay = AsyncMock(return_value=triple_ok)
        MockBuilder.return_value = mock_builder

        await client.post(
            "/api/parlay/suggest",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "num_legs": 3,
                "risk_profile": "balanced",
                "request_mode": "TRIPLE",
                "sports": ["NFL"],
            },
        )

    # Exactly one call with request_mode=TRIPLE; no retries with week=None or ml_only
    assert mock_builder.build_parlay.call_count == 1
    call_kwargs = mock_builder.build_parlay.call_args[1]
    assert call_kwargs.get("request_mode") == "TRIPLE"
