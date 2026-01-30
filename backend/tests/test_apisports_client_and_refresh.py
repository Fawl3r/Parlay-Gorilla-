"""
Unit tests for ApiSportsClient.request success path and SportsRefreshService.run_refresh.

Prevents regressions: undefined sport_key in client (NameError on 200 response),
undefined active_sports in refresh service (NameError in loop).
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.apisports.client import ApiSportsClient
from app.services.sports_refresh_service import SportsRefreshService


# --- ApiSportsClient.request: no NameError on 200, quota success path called ---


@pytest.mark.asyncio
async def test_apisports_client_request_200_does_not_raise_name_error():
    """On simulated 200 response, request() returns data and does not raise NameError."""
    client = ApiSportsClient(
        base_url="https://test.example",
        api_key="test-key",
    )
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"response": []}
    mock_http = AsyncMock()
    mock_http.request = AsyncMock(return_value=mock_resp)
    mock_ac = MagicMock()
    mock_ac.__aenter__ = AsyncMock(return_value=mock_http)
    mock_ac.__aexit__ = AsyncMock(return_value=None)

    with (
        patch("app.services.apisports.client.httpx.AsyncClient", return_value=mock_ac),
        patch.object(client, "_quota") as quota,
        patch.object(client, "_rate_limiter") as limiter,
    ):
        quota.can_spend = AsyncMock(return_value=True)
        quota.spend = AsyncMock(return_value=None)
        quota.record_success = AsyncMock(return_value=None)
        limiter.acquire = AsyncMock(return_value=True)
        result = await client.request("/fixtures", sport="icehockey_nhl")

    assert result is not None
    assert result == {"response": []}


@pytest.mark.asyncio
async def test_apisports_client_request_200_calls_after_success_with_sport():
    """On 200 response, _after_success is called with n=1 and sport so quota is tracked per sport."""
    client = ApiSportsClient(
        base_url="https://test.example",
        api_key="test-key",
    )
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"response": []}
    mock_http = AsyncMock()
    mock_http.request = AsyncMock(return_value=mock_resp)
    mock_ac = MagicMock()
    mock_ac.__aenter__ = AsyncMock(return_value=mock_http)
    mock_ac.__aexit__ = AsyncMock(return_value=None)

    with (
        patch("app.services.apisports.client.httpx.AsyncClient", return_value=mock_ac),
        patch.object(client, "_quota") as quota,
        patch.object(client, "_rate_limiter") as limiter,
        patch.object(client, "_after_success", new_callable=AsyncMock) as after_success,
    ):
        quota.can_spend = AsyncMock(return_value=True)
        limiter.acquire = AsyncMock(return_value=True)
        await client.request("/standings", params={"league": 57, "season": 2024}, sport="icehockey_nhl")

    after_success.assert_called_once()
    call_kw = after_success.call_args[1]
    assert call_kw.get("sport") == "icehockey_nhl"
    assert after_success.call_args[0][0] == 1


# --- SportsRefreshService.run_refresh: no NameError, uses computed active_sports ---


@pytest.mark.asyncio
async def test_sports_refresh_run_refresh_uses_active_sports_no_name_error(db):
    """run_refresh() does not raise NameError and uses the list from _active_sports_for_next_48h."""
    with (
        patch("app.services.sports_refresh_service.get_apisports_client") as get_client,
        patch("app.services.sports_refresh_service.get_quota_manager") as get_quota,
    ):
        mock_client = MagicMock()
        mock_client.is_configured.return_value = True
        mock_client.get_fixtures = AsyncMock(return_value=None)
        mock_client.get_standings = AsyncMock(return_value=None)
        get_client.return_value = mock_client

        mock_quota = MagicMock()
        mock_quota.remaining_async = AsyncMock(return_value=50)
        mock_quota.can_spend = AsyncMock(return_value=True)
        get_quota.return_value = mock_quota

        service = SportsRefreshService(db)
        # Override _active_sports_for_next_48h to return a fixed list so we know the loop ran
        service._active_sports_for_next_48h = AsyncMock(return_value=["icehockey_nhl"])

        result = await service.run_refresh()

    assert "used" in result
    assert "remaining" in result
    assert "refreshed" in result
    assert result["refreshed"].get("fixtures", 0) >= 0
    service._active_sports_for_next_48h.assert_called_once()
