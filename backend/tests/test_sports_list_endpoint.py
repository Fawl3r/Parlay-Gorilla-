import pytest
from unittest.mock import AsyncMock, patch


# Analysis hub (and other UIs) tab ids; /api/sports must return a slug for each (lowercased match).
# Prevents "new tab added but backend missing" or "slug mismatch" regressions.
EXPECTED_ANALYSIS_HUB_TAB_IDS = ["nfl", "nba", "nhl", "mlb", "ncaaf", "ncaab", "epl", "mls"]


@pytest.mark.asyncio
async def test_list_sports_hides_ucl_and_marks_combat_sports_coming_soon(client):
    resp = await client.get("/api/sports")
    assert resp.status_code == 200

    data = resp.json()
    assert isinstance(data, list)

    slugs = {item.get("slug") for item in data if isinstance(item, dict)}
    assert "ucl" not in slugs

    ufc = next((item for item in data if isinstance(item, dict) and item.get("slug") == "ufc"), None)
    boxing = next((item for item in data if isinstance(item, dict) and item.get("slug") == "boxing"), None)

    assert ufc is not None
    assert boxing is not None

    assert ufc.get("in_season") is False
    assert boxing.get("in_season") is False
    assert ufc.get("is_enabled") is False
    assert boxing.get("is_enabled") is False

    assert ufc.get("status_label") == "Coming Soon"
    assert boxing.get("status_label") == "Coming Soon"


@pytest.mark.asyncio
async def test_list_sports_availability_contract_and_cache_control(client):
    """Every sport has slug, sport_state, is_enabled; /api/sports has short cache; tab ids exist."""
    resp = await client.get("/api/sports")
    assert resp.status_code == 200

    # Cache-Control: short TTL so Cloudflare doesn't mask preseason unlock / is_enabled flips
    cache_control = resp.headers.get("Cache-Control", "")
    assert "max-age=60" in cache_control, f"Expected max-age=60 in Cache-Control for /api/sports, got {cache_control}"

    data = resp.json()
    assert isinstance(data, list)

    slugs_lower = set()
    for i, item in enumerate(data):
        assert isinstance(item, dict), f"item[{i}] not a dict"
        assert "slug" in item, f"item[{i}] missing slug"
        assert "sport_state" in item, f"item[{i}] (slug={item.get('slug')}) missing sport_state"
        assert "is_enabled" in item, f"item[{i}] (slug={item.get('slug')}) missing is_enabled"
        slugs_lower.add((item.get("slug") or "").lower())

    for tab_id in EXPECTED_ANALYSIS_HUB_TAB_IDS:
        assert tab_id.lower() in slugs_lower, (
            f"Availability contract: UI tab id {tab_id!r} not found in /api/sports slugs. "
            "Add to backend or remove from frontend SPORT_TABS."
        )


@pytest.mark.asyncio
async def test_list_sports_does_not_500_if_state_service_errors(client):
    """Regression: /api/sports must not 500 if sport_state inference fails."""
    with patch(
        "app.api.routes.sports.get_sport_state",
        new_callable=AsyncMock,
        side_effect=RuntimeError("boom"),
    ):
        resp = await client.get("/api/sports")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        for item in data:
            assert isinstance(item, dict)
            assert "slug" in item
            assert "sport_state" in item
            assert "is_enabled" in item





