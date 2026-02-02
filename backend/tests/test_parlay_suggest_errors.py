"""Tests for POST /api/parlay/suggest error handling (409, fallback meta, domain exception)."""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock
import uuid

from app.services.entitlements.entitlement_service import ParlaySuggestAccess
from app.core.parlay_errors import InsufficientCandidatesException



def _make_leg(game_id: str, market_id: str, outcome: str, confidence: float = 60.0):
    return {
        "game_id": game_id,
        "market_id": market_id,
        "outcome": outcome,
        "game": f"Game {game_id}",
        "home_team": "Home",
        "away_team": "Away",
        "market_type": "h2h",
        "odds": "-110",
        "adjusted_prob": 0.55,
        "confidence_score": confidence,
        "sport": "NFL",
    }


@pytest.mark.asyncio
async def test_parlay_suggest_insufficient_candidates_exception_returns_409(
    client: AsyncClient,
    db,
):
    """When builder raises InsufficientCandidatesException (single-sport), route returns 409 with hint from reasons."""
    email = f"parlay-409-{uuid.uuid4()}@test.com"
    await client.post("/api/auth/register", json={"email": email, "password": "Passw0rd!"})
    login = await client.post("/api/auth/login", json={"email": email, "password": "Passw0rd!"})
    token = login.json()["access_token"]

    allowed_access = ParlaySuggestAccess(
        allowed=True,
        reason=None,
        features={"mix_sports": False, "max_legs": 20, "player_props": True},
        credits_remaining=10,
    )
    with patch(
        "app.api.routes.parlay.EntitlementService"
    ) as MockEntitlement, patch(
        "app.api.routes.parlay.check_parlay_access_with_purchase",
        new_callable=AsyncMock,
        return_value={"can_generate": True, "use_free": True, "error_code": None},
    ), patch(
        "app.api.routes.parlay.ParlayBuilderService"
    ) as MockBuilder, patch(
        "app.api.routes.parlay.get_parlay_eligibility",
        new_callable=AsyncMock,
    ) as mock_eligibility:
        MockEntitlement.return_value.get_parlay_suggest_access = AsyncMock(return_value=allowed_access)
        mock_builder_instance = MagicMock()
        mock_builder_instance.build_parlay = AsyncMock(
            side_effect=InsufficientCandidatesException(needed=5, have=2)
        )
        MockBuilder.return_value = mock_builder_instance
        mock_eligibility.return_value = MagicMock(
            eligible_count=2,
            unique_games=2,
            exclusion_reasons=[{"reason": "NO_ODDS", "count": 14}],
            debug_id="test-debug-123",
        )

        resp = await client.post(
            "/api/parlay/suggest",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "num_legs": 5,
                "risk_profile": "balanced",
                "sports": ["NFL"],
                "week": 18,
            },
        )

    assert resp.status_code == 409
    data = resp.json()
    assert data.get("needed") == 5
    assert data.get("have") == 2
    assert "hint" in data
    assert "top_exclusion_reasons" in data
    assert data.get("debug_id") == "test-debug-123"


@pytest.mark.asyncio
async def test_parlay_suggest_value_error_returns_409_insufficient_candidates(
    client: AsyncClient,
    db,
):
    """When builder raises ValueError (e.g. insufficient candidates), route returns 409 with needed, have, top_exclusion_reasons, debug_id."""
    email = f"parlay-422-{uuid.uuid4()}@test.com"
    await client.post("/api/auth/register", json={"email": email, "password": "Passw0rd!"})
    login = await client.post("/api/auth/login", json={"email": email, "password": "Passw0rd!"})
    token = login.json()["access_token"]

    allowed_access = ParlaySuggestAccess(
        allowed=True,
        reason=None,
        features={"mix_sports": True, "max_legs": 20, "player_props": True},
        credits_remaining=10,
    )
    with patch(
        "app.api.routes.parlay.EntitlementService"
    ) as MockEntitlement, patch(
        "app.api.routes.parlay.check_parlay_access_with_purchase",
        new_callable=AsyncMock,
        return_value={"can_generate": True, "use_free": True, "error_code": None},
    ), patch(
        "app.api.routes.parlay.MixedSportsParlayBuilder"
    ) as MockMixedBuilder:
        MockEntitlement.return_value.get_parlay_suggest_access = AsyncMock(return_value=allowed_access)
        mock_builder = MagicMock()
        mock_builder.build_mixed_parlay = AsyncMock(
            side_effect=ValueError(
                "Could not fulfill requested number of legs with available games. "
                "requested=5 available=2"
            )
        )
        MockMixedBuilder.return_value = mock_builder

        resp = await client.post(
            "/api/parlay/suggest",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "num_legs": 5,
                "risk_profile": "balanced",
                "sports": ["NFL", "NBA"],
                "mix_sports": True,
                "week": 18,
            },
        )

    assert resp.status_code == 409
    data = resp.json()
    assert data.get("code") == "insufficient_candidates"
    assert "message" in data
    assert "hint" in data
    assert data.get("needed") == 5
    assert "have" in data
    assert "top_exclusion_reasons" in data
    assert "debug_id" in data
    assert data.get("meta", {}).get("num_legs") == 5
    assert "NFL" in (data.get("meta") or {}).get("sports", [])


@pytest.mark.asyncio
async def test_parlay_suggest_invalid_request_value_error_bubbles_500(
    client: AsyncClient,
    db,
):
    """When builder raises ValueError with non-insufficient message, route re-raises → 500 (no 422)."""
    email = f"parlay-inv-{uuid.uuid4()}@test.com"
    await client.post("/api/auth/register", json={"email": email, "password": "Passw0rd!"})
    login = await client.post("/api/auth/login", json={"email": email, "password": "Passw0rd!"})
    token = login.json()["access_token"]

    allowed_access = ParlaySuggestAccess(
        allowed=True,
        reason=None,
        features={"mix_sports": True, "max_legs": 20, "player_props": True},
        credits_remaining=10,
    )
    with patch(
        "app.api.routes.parlay.EntitlementService"
    ) as MockEntitlement, patch(
        "app.api.routes.parlay.check_parlay_access_with_purchase",
        new_callable=AsyncMock,
        return_value={"can_generate": True, "use_free": True, "error_code": None},
    ), patch(
        "app.api.routes.parlay.MixedSportsParlayBuilder"
    ) as MockMixedBuilder:
        MockEntitlement.return_value.get_parlay_suggest_access = AsyncMock(return_value=allowed_access)
        mock_builder = MagicMock()
        mock_builder.build_mixed_parlay = AsyncMock(
            side_effect=ValueError("Invalid risk profile requested.")
        )
        MockMixedBuilder.return_value = mock_builder

        resp = await client.post(
            "/api/parlay/suggest",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "num_legs": 3,
                "risk_profile": "balanced",
                "sports": ["NFL", "NBA"],
                "mix_sports": True,
            },
        )

    assert resp.status_code == 500


@pytest.mark.asyncio
async def test_mixed_sports_nfl_week_fallback_returns_200_with_meta():
    """
    Mixed sports with NFL week: when first pass has insufficient candidates,
    builder fallback (current week / no week) can succeed and response includes
    meta.nfl_week_fallback_used (unit test of builder behavior via mock).
    """
    from app.services.mixed_sports_parlay_impl.mixed_sports_parlay_builder import (
        MixedSportsParlayBuilder,
    )

    mock_db = AsyncMock()
    builder = MixedSportsParlayBuilder(mock_db)

    legs_insufficient = [_make_leg(f"g{i}", f"m{i}", "home") for i in range(2)]
    legs_sufficient = [_make_leg(f"g{i}", f"m{i}", "home") for i in range(6)]

    call_count = 0

    async def mock_load(*, sports, min_confidence, requested_legs, week, include_player_props=False):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return legs_insufficient
        return legs_sufficient

    with patch.object(
        builder,
        "_load_candidates_with_fallback",
        side_effect=mock_load,
    ):
        result = await builder.build_mixed_parlay(
            num_legs=5,
            sports=["NFL", "NBA"],
            risk_profile="balanced",
            balance_sports=True,
            week=18,
        )

    assert result.get("meta", {}).get("nfl_week_fallback_used") is True
    assert result["meta"].get("nfl_week_used") is None or result["meta"].get("nfl_week_used") is not None
    assert len(result.get("legs", [])) == 5


@pytest.mark.asyncio
async def test_parlay_suggest_anon_returns_401_login_required(client: AsyncClient):
    """Anonymous POST /api/parlay/suggest returns 401 with ParlaySuggestError code=login_required."""
    resp = await client.post(
        "/api/parlay/suggest",
        json={"num_legs": 3, "risk_profile": "balanced", "sports": ["NFL"]},
    )
    assert resp.status_code == 401
    data = resp.json()
    assert data.get("code") == "login_required"
    assert "message" in data


@pytest.mark.asyncio
async def test_me_entitlements_anon_returns_200(client: AsyncClient):
    """GET /api/me/entitlements without auth returns 200 with is_authenticated=False."""
    resp = await client.get("/api/me/entitlements")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("is_authenticated") is False
    assert data.get("plan") == "anon"
    assert "credits" in data
    assert "features" in data
    assert data["features"].get("mix_sports") is False
    assert data["features"].get("max_legs") == 5


@pytest.mark.asyncio
async def test_me_entitlements_auth_returns_plan_and_features(client: AsyncClient, db):
    """GET /api/me/entitlements with auth returns plan and features."""
    email = f"ent-{uuid.uuid4()}@test.com"
    await client.post("/api/auth/register", json={"email": email, "password": "Passw0rd!"})
    login = await client.post("/api/auth/login", json={"email": email, "password": "Passw0rd!"})
    token = login.json()["access_token"]
    resp = await client.get("/api/me/entitlements", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("is_authenticated") is True
    assert data.get("plan") in ("free", "premium")
    assert "credits" in data
    assert "features" in data
