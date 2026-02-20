from datetime import datetime, timezone

import pytest

from app.services.data_fetchers.weather import WeatherFetcher


@pytest.mark.asyncio
async def test_weather_fetcher_falls_back_when_coords_unknown(monkeypatch):
    fetcher = WeatherFetcher()
    fetcher.api_key = "test-key"

    # Force unknown coordinates so we exercise fallback behavior.
    monkeypatch.setattr(fetcher, "_get_stadium_coords", lambda home_team, location=None: None)

    weather = await fetcher.get_game_weather(
        home_team="Unknown FC",
        game_time=datetime(2026, 2, 20, 20, 0, tzinfo=timezone.utc),
    )

    assert isinstance(weather, dict)
    assert "is_outdoor" in weather
    assert "temperature" in weather
