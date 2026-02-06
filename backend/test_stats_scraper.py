"""Test stats scraper service"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

print("Testing Stats Scraper Service...")


def test_stats_scraper_import():
    """Test that StatsScraperService can be imported"""
    from app.services.stats_scraper import StatsScraperService
    assert StatsScraperService is not None
    print("✓ StatsScraperService imported successfully")


def test_stats_scraper_methods():
    """Test that StatsScraperService has expected methods"""
    from app.services.stats_scraper import StatsScraperService
    
    assert hasattr(StatsScraperService, 'get_team_stats')
    assert hasattr(StatsScraperService, 'get_weather_data')
    assert hasattr(StatsScraperService, 'get_injury_report')
    assert hasattr(StatsScraperService, 'get_matchup_data')
    assert hasattr(StatsScraperService, 'clear_cache')
    print("✓ All expected methods present")


def test_weather_impact_assessment():
    """Test weather impact assessment logic"""
    from app.services.stats_scraper import StatsScraperService
    
    # Create mock db session
    mock_db = MagicMock()
    scraper = StatsScraperService(mock_db)
    
    # Test rainy conditions
    weather_rain = {
        "weather": [{"main": "Rain"}],
        "wind": {"speed": 5},
        "main": {"temp": 65}
    }
    impact = scraper._assess_weather_impact(weather_rain)
    assert "running game" in impact.lower() or "passing" in impact.lower()
    print("✓ Rain weather impact assessment works")
    
    # Test windy conditions
    weather_wind = {
        "weather": [{"main": "Clear"}],
        "wind": {"speed": 20},
        "main": {"temp": 65}
    }
    impact = scraper._assess_weather_impact(weather_wind)
    assert "wind" in impact.lower()
    print("✓ Wind weather impact assessment works")
    
    # Test cold conditions
    weather_cold = {
        "weather": [{"main": "Clear"}],
        "wind": {"speed": 5},
        "main": {"temp": 25}
    }
    impact = scraper._assess_weather_impact(weather_cold)
    assert "freez" in impact.lower() or "cold" in impact.lower()
    print("✓ Cold weather impact assessment works")
    
    # Test normal conditions
    weather_normal = {
        "weather": [{"main": "Clear"}],
        "wind": {"speed": 5},
        "main": {"temp": 70}
    }
    impact = scraper._assess_weather_impact(weather_normal)
    assert "not significantly impact" in impact.lower()
    print("✓ Normal weather impact assessment works")


@pytest.mark.asyncio
async def test_stats_scraper_cache():
    """Test that stats scraper caching works"""
    from app.services.stats_scraper import StatsScraperService
    
    mock_db = MagicMock()
    scraper = StatsScraperService(mock_db)
    
    # Check cache is initially empty
    assert len(scraper._cache) == 0
    print("✓ Cache is initially empty")
    
    # Test clear_cache method
    scraper._cache["test_key"] = ("test_data", datetime.now())
    assert len(scraper._cache) == 1
    scraper.clear_cache()
    assert len(scraper._cache) == 0
    print("✓ clear_cache method works")


@pytest.mark.asyncio
async def test_get_injury_report():
    """Test injury report returns expected structure"""
    from app.services.stats_scraper import StatsScraperService
    
    mock_db = MagicMock()
    scraper = StatsScraperService(mock_db)
    
    # Get injury report (should return placeholder)
    report = await scraper.get_injury_report("Green Bay Packers", "NFL")
    
    assert "key_players_out" in report
    assert "injury_summary" in report
    assert "impact_assessment" in report
    print("✓ Injury report returns expected structure")


@pytest.mark.asyncio
async def test_get_injury_report_uses_espn_resolver_when_no_team_abbr():
    """When API-Sports cache is empty, ESPN resolver path is used (team_abbr not required)."""
    from app.services.stats_scraper import StatsScraperService
    from app.services.espn.espn_team_resolver import ResolvedTeamRef

    mock_db = MagicMock()
    scraper = StatsScraperService(mock_db)
    scraper.clear_cache()
    scraper._team_mapper.get_team_id = MagicMock(return_value=None)

    mock_ref = ResolvedTeamRef(
        team_id="20",
        injuries_url="https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/teams/20/injuries",
        team_url=None,
        matched_name="Vegas Golden Knights",
        match_method="exact",
        confidence=1.0,
    )
    mock_injury_data = {
        "key_players_out": [{"name": "Player A", "position": "C", "status": "Out"}],
        "injury_severity_score": 0.5,
        "total_injured": 1,
        "summary": "1 key player out",
        "unit_counts": {},
    }

    with patch("app.services.espn.espn_team_resolver.EspnTeamResolver") as MockResolver, \
         patch("app.services.espn.espn_injuries_client.EspnInjuriesClient") as MockClient:
        mock_resolver_instance = MagicMock()
        mock_resolver_instance.resolve_team_ref = AsyncMock(return_value=mock_ref)
        MockResolver.return_value = mock_resolver_instance
        mock_client_instance = MagicMock()
        mock_client_instance.fetch_injuries_for_team_ref = AsyncMock(return_value=mock_injury_data)
        MockClient.return_value = mock_client_instance

        report = await scraper.get_injury_report("Vegas Golden Knights", "NHL")

    assert "key_players_out" in report
    assert report["total_injured"] == 1
    assert "Player A" in report.get("injury_summary", "")
    assert "impact_assessment" in report
    mock_resolver_instance.resolve_team_ref.assert_called_once()
    mock_client_instance.fetch_injuries_for_team_ref.assert_called_once()
    print("✓ ESPN resolver path used when team_abbr not required")


if __name__ == "__main__":
    print("=" * 60)
    print("Running Stats Scraper Tests")
    print("=" * 60)
    
    test_stats_scraper_import()
    test_stats_scraper_methods()
    test_weather_impact_assessment()
    asyncio.run(test_stats_scraper_cache())
    asyncio.run(test_get_injury_report())
    
    print("\n" + "=" * 60)
    print("All stats scraper tests passed!")
    print("=" * 60)

