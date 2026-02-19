import pytest
from unittest.mock import AsyncMock, patch


# Analysis hub (and other UIs) tab ids; /api/sports must return a slug for each (lowercased match).
# Prevents "new tab added but backend missing" or "slug mismatch" regressions.
EXPECTED_ANALYSIS_HUB_TAB_IDS = ["nfl", "nba", "wnba", "nhl", "mlb", "ncaaf", "ncaab", "epl", "mls"]


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


@pytest.mark.asyncio
async def test_games_list_accepts_wnba_sport(client):
    """Games list endpoint must accept sport=wnba and return 200 (same contract as other sports)."""
    resp = await client.get("/api/sports/wnba/games")
    assert resp.status_code == 200
    data = resp.json()
    assert "games" in data
    assert isinstance(data["games"], list)
    assert "sport_state" in data
    assert "status_label" in data


@pytest.mark.asyncio
async def test_wnba_always_visible_in_sports_list(client):
    """WNBA must appear in /api/sports year-round (visibility=visible); can show OFFSEASON when no games."""
    resp = await client.get("/api/sports")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    wnba = next((item for item in data if isinstance(item, dict) and (item.get("slug") or "").lower() == "wnba"), None)
    assert wnba is not None, "WNBA must be in /api/sports (visible year-round)"
    assert "sport_state" in wnba
    assert wnba["sport_state"] in ("OFFSEASON", "PRESEASON", "IN_SEASON", "IN_BREAK", "POSTSEASON")
    assert "is_enabled" in wnba


@pytest.mark.asyncio
async def test_wnba_sport_state_offseason_when_mocked(client):
    """When get_sport_state returns OFFSEASON for WNBA, /api/sports wnba item has sport_state OFFSEASON."""
    async def mock_state(*args, **kwargs):
        sport_code = kwargs.get("sport_code") or (args[1] if len(args) > 1 else "")
        if (sport_code or "").upper() == "WNBA":
            return {
                "sport_state": "OFFSEASON",
                "next_game_at": None,
                "last_game_at": None,
                "state_reason": "no_games",
                "is_enabled": False,
                "days_to_next": None,
                "preseason_enable_days": None,
                "upcoming_soon_count": 0,
                "recent_count": 0,
            }
        # Default for other sports
        return {
            "sport_state": "IN_SEASON",
            "next_game_at": "2025-03-01T00:00:00Z",
            "last_game_at": None,
            "state_reason": "upcoming",
            "is_enabled": True,
            "days_to_next": 10,
            "preseason_enable_days": 14,
            "upcoming_soon_count": 5,
            "recent_count": 0,
        }

    with patch("app.api.routes.sports.get_sport_state", new_callable=AsyncMock, side_effect=mock_state):
        resp = await client.get("/api/sports")
        assert resp.status_code == 200
        data = resp.json()
        wnba = next((item for item in data if isinstance(item, dict) and (item.get("slug") or "").lower() == "wnba"), None)
        assert wnba is not None
        assert wnba["sport_state"] == "OFFSEASON"
        assert wnba["status_label"] == "Offseason"


@pytest.mark.asyncio
async def test_wnba_sport_state_in_season_when_mocked(client):
    """When get_sport_state returns IN_SEASON for WNBA, /api/sports wnba item reflects it."""
    async def mock_state(*args, **kwargs):
        sport_code = kwargs.get("sport_code") or (args[1] if len(args) > 1 else "")
        if (sport_code or "").upper() == "WNBA":
            return {
                "sport_state": "IN_SEASON",
                "next_game_at": "2025-06-15T00:00:00Z",
                "last_game_at": "2025-06-10T00:00:00Z",
                "state_reason": "upcoming",
                "is_enabled": True,
                "days_to_next": 5,
                "preseason_enable_days": 14,
                "upcoming_soon_count": 12,
                "recent_count": 8,
            }
        return {
            "sport_state": "OFFSEASON",
            "next_game_at": None,
            "last_game_at": None,
            "state_reason": "no_games",
            "is_enabled": False,
            "days_to_next": None,
            "preseason_enable_days": None,
            "upcoming_soon_count": 0,
            "recent_count": 0,
        }

    with patch("app.api.routes.sports.get_sport_state", new_callable=AsyncMock, side_effect=mock_state):
        resp = await client.get("/api/sports")
        assert resp.status_code == 200
        data = resp.json()
        wnba = next((item for item in data if isinstance(item, dict) and (item.get("slug") or "").lower() == "wnba"), None)
        assert wnba is not None
        assert wnba["sport_state"] == "IN_SEASON"
        assert wnba["status_label"] == "In season"





