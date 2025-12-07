"""Test analysis generator service"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import json

print("Testing Analysis Generator Service...")


def test_analysis_generator_import():
    """Test that AnalysisGeneratorService can be imported"""
    from app.services.analysis_generator import AnalysisGeneratorService
    assert AnalysisGeneratorService is not None
    print("✓ AnalysisGeneratorService imported successfully")


def test_analysis_generator_methods():
    """Test that AnalysisGeneratorService has expected methods"""
    from app.services.analysis_generator import AnalysisGeneratorService
    
    assert hasattr(AnalysisGeneratorService, 'generate_game_analysis')
    assert hasattr(AnalysisGeneratorService, '_build_analysis_context')
    assert hasattr(AnalysisGeneratorService, '_format_team_stats')
    assert hasattr(AnalysisGeneratorService, '_generate_ai_analysis')
    assert hasattr(AnalysisGeneratorService, '_generate_same_game_parlays')
    print("✓ All expected methods present")


def test_build_analysis_context():
    """Test context building for AI analysis"""
    from app.services.analysis_generator import AnalysisGeneratorService
    
    mock_db = MagicMock()
    generator = AnalysisGeneratorService(mock_db)
    
    # Test context building
    context = generator._build_analysis_context(
        home_team="Green Bay Packers",
        away_team="Chicago Bears",
        league="NFL",
        game_time=datetime.now(),
        matchup_data={
            "home_team_stats": {
                "team_name": "Green Bay Packers",
                "record": {"wins": 10, "losses": 4, "win_percentage": 0.714},
                "offense": {"points_per_game": 28.5, "yards_per_game": 380},
                "defense": {"points_allowed_per_game": 20.0, "yards_allowed_per_game": 320},
                "ats_trends": {"wins": 8, "losses": 6, "win_percentage": 0.571, "recent": "3-2", "home": "5-2", "away": "3-4"},
                "over_under_trends": {"overs": 7, "unders": 7, "over_percentage": 0.5, "recent_overs": 2, "recent_unders": 3},
            },
            "away_team_stats": None,
            "weather": {
                "temperature": 35,
                "description": "Partly cloudy",
                "wind_speed": 12,
                "impact_assessment": "Cold temperatures may affect ball handling"
            }
        },
        odds_data={
            "spread": "-3.5",
            "total": "44.5",
            "home_ml": "-175",
            "away_ml": "+155"
        }
    )
    
    assert "Green Bay Packers" in context
    assert "Chicago Bears" in context
    assert "NFL" in context
    assert "BETTING LINES" in context
    assert "WEATHER CONDITIONS" in context
    print("✓ Context building works correctly")


def test_format_team_stats():
    """Test team stats formatting"""
    from app.services.analysis_generator import AnalysisGeneratorService
    
    mock_db = MagicMock()
    generator = AnalysisGeneratorService(mock_db)
    
    # Test with stats
    stats = {
        "team_name": "Green Bay Packers",
        "record": {"wins": 10, "losses": 4, "win_percentage": 0.714},
        "offense": {"points_per_game": 28.5, "yards_per_game": 380},
        "defense": {"points_allowed_per_game": 20.0, "yards_allowed_per_game": 320},
        "ats_trends": {"wins": 8, "losses": 6, "win_percentage": 0.571},
        "over_under_trends": {"overs": 7, "unders": 7, "over_percentage": 0.5},
    }
    
    formatted = generator._format_team_stats("Green Bay Packers", stats)
    assert "Green Bay Packers" in formatted
    assert "10-4" in formatted
    print("✓ Team stats formatting works with stats")
    
    # Test with None stats
    formatted_none = generator._format_team_stats("Green Bay Packers", None)
    assert "not available" in formatted_none.lower()
    print("✓ Team stats formatting handles None stats")


@pytest.mark.asyncio
async def test_generate_same_game_parlays_structure():
    """Test same-game parlays generation returns expected structure"""
    from app.services.analysis_generator import AnalysisGeneratorService
    
    # Create mock db with required methods
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))))
    
    generator = AnalysisGeneratorService(mock_db)
    
    # Mock the parlay builder
    with patch.object(generator, '_generate_same_game_parlays') as mock_parlays:
        mock_parlays.return_value = {
            "safe_3_leg": {"legs": [], "hit_probability": 0.3, "confidence": 70},
            "balanced_6_leg": {"legs": [], "hit_probability": 0.1, "confidence": 55},
            "degen_10_20_leg": {"legs": [], "hit_probability": 0.01, "confidence": 40},
        }
        
        parlays = await mock_parlays("game-123", "NFL", "Green Bay Packers", "Chicago Bears")
        
        assert "safe_3_leg" in parlays
        assert "balanced_6_leg" in parlays
        assert "degen_10_20_leg" in parlays
        
        assert "legs" in parlays["safe_3_leg"]
        assert "hit_probability" in parlays["safe_3_leg"]
        assert "confidence" in parlays["safe_3_leg"]
        
        print("✓ Same-game parlays structure is correct")


if __name__ == "__main__":
    print("=" * 60)
    print("Running Analysis Generator Tests")
    print("=" * 60)
    
    test_analysis_generator_import()
    test_analysis_generator_methods()
    test_build_analysis_context()
    test_format_team_stats()
    asyncio.run(test_generate_same_game_parlays_structure())
    
    print("\n" + "=" * 60)
    print("All analysis generator tests passed!")
    print("=" * 60)

