"""Test analysis models and database schema"""

import asyncio
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Test imports
print("Testing Analysis Model Imports...")


def test_game_analysis_model_import():
    """Test that GameAnalysis model can be imported"""
    from app.models.game_analysis import GameAnalysis
    assert GameAnalysis is not None
    print("✓ GameAnalysis model imported successfully")
    
    # Check model has expected columns
    assert hasattr(GameAnalysis, 'id')
    assert hasattr(GameAnalysis, 'game_id')
    assert hasattr(GameAnalysis, 'slug')
    assert hasattr(GameAnalysis, 'league')
    assert hasattr(GameAnalysis, 'matchup')
    assert hasattr(GameAnalysis, 'analysis_content')
    assert hasattr(GameAnalysis, 'seo_metadata')
    assert hasattr(GameAnalysis, 'generated_at')
    assert hasattr(GameAnalysis, 'expires_at')
    assert hasattr(GameAnalysis, 'version')
    print("✓ All expected columns present")


def test_team_stats_model_ats_fields():
    """Test that TeamStats model has ATS trend fields"""
    from app.models.team_stats import TeamStats
    assert TeamStats is not None
    print("✓ TeamStats model imported successfully")
    
    # Check ATS fields
    assert hasattr(TeamStats, 'ats_wins')
    assert hasattr(TeamStats, 'ats_losses')
    assert hasattr(TeamStats, 'ats_pushes')
    assert hasattr(TeamStats, 'ats_win_percentage')
    assert hasattr(TeamStats, 'ats_recent_wins')
    assert hasattr(TeamStats, 'ats_recent_losses')
    assert hasattr(TeamStats, 'ats_home_wins')
    assert hasattr(TeamStats, 'ats_home_losses')
    assert hasattr(TeamStats, 'ats_away_wins')
    assert hasattr(TeamStats, 'ats_away_losses')
    print("✓ ATS trend fields present")
    
    # Check O/U fields
    assert hasattr(TeamStats, 'over_wins')
    assert hasattr(TeamStats, 'under_wins')
    assert hasattr(TeamStats, 'over_percentage')
    assert hasattr(TeamStats, 'over_recent_count')
    assert hasattr(TeamStats, 'under_recent_count')
    assert hasattr(TeamStats, 'avg_total_points')
    print("✓ O/U trend fields present")


def test_analysis_schema_import():
    """Test that analysis schemas can be imported"""
    from app.schemas.analysis import (
        GameAnalysisResponse,
        GameAnalysisListItem,
        AnalysisGenerationRequest,
        SpreadPick,
        TotalPick,
        BestBet,
        ModelWinProbability,
        MatchupEdges,
        TrendAnalysis,
        SameGameParlay,
        SameGameParlays,
        GameAnalysisContent,
    )
    
    print("✓ All analysis schemas imported successfully")
    
    # Test schema validation
    spread_pick = SpreadPick(pick="Home -3.5", confidence=72, rationale="Strong home team")
    assert spread_pick.pick == "Home -3.5"
    assert spread_pick.confidence == 72
    print("✓ SpreadPick schema validation works")
    
    best_bet = BestBet(bet_type="Spread", pick="Home -3.5", confidence=72, rationale="Test")
    assert best_bet.bet_type == "Spread"
    print("✓ BestBet schema validation works")
    
    win_prob = ModelWinProbability(home_win_prob=0.6, away_win_prob=0.4, explanation="Test")
    assert win_prob.home_win_prob == 0.6
    print("✓ ModelWinProbability schema validation works")


def test_models_registered_in_init():
    """Test that GameAnalysis is registered in models __init__"""
    from app.models import GameAnalysis
    assert GameAnalysis is not None
    print("✓ GameAnalysis registered in models __init__")


if __name__ == "__main__":
    print("=" * 60)
    print("Running Analysis Model Tests")
    print("=" * 60)
    
    test_game_analysis_model_import()
    test_team_stats_model_ats_fields()
    test_analysis_schema_import()
    test_models_registered_in_init()
    
    print("\n" + "=" * 60)
    print("All model tests passed!")
    print("=" * 60)

