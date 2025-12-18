"""Comprehensive tests for game analysis generation including ATS/O/U integration"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from datetime import datetime, timedelta
from types import SimpleNamespace

from app.services.analysis_generator import AnalysisGeneratorService
from app.models.game import Game
from app.models.market import Market
from app.models.odds import Odds


class TestGameAnalysisGeneration:
    """Tests for full game analysis generation flow"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        db = AsyncMock()
        db.execute = AsyncMock()
        return db
    
    @pytest.fixture
    def mock_game(self):
        """Create a mock game object"""
        game = MagicMock(spec=Game)
        game.id = uuid.uuid4()
        game.sport = "NFL"
        game.home_team = "Green Bay Packers"
        game.away_team = "Chicago Bears"
        game.start_time = datetime.now() + timedelta(days=1)
        game.status = "scheduled"
        return game
    
    @pytest.fixture
    def mock_markets(self):
        """Create mock markets with spread and total"""
        # Create odds objects without spec to allow dynamic attributes
        spread_odds_home = MagicMock()
        spread_odds_home.outcome = "home -3.5"
        spread_odds_home.price = "-110"
        
        spread_odds_away = MagicMock()
        spread_odds_away.outcome = "away +3.5"
        spread_odds_away.price = "-110"
        
        spread_market = MagicMock()
        spread_market.market_type = "spreads"
        spread_market.id = "spread-market-1"
        spread_market.book = "draftkings"
        spread_market.odds = [spread_odds_home, spread_odds_away]
        
        total_odds_over = MagicMock()
        total_odds_over.outcome = "over 44.5"
        total_odds_over.price = "-110"
        
        total_odds_under = MagicMock()
        total_odds_under.outcome = "under 44.5"
        total_odds_under.price = "-110"
        
        total_market = MagicMock()
        total_market.market_type = "totals"
        total_market.id = "total-market-1"
        total_market.book = "draftkings"
        total_market.odds = [total_odds_over, total_odds_under]
        
        return [spread_market, total_market]
    
    @pytest.fixture
    def mock_matchup_data(self):
        """Create mock matchup data with ATS/O/U trends"""
        return {
            "home_team_stats": {
                "team_name": "Green Bay Packers",
                "record": {"wins": 10, "losses": 4},
                "offense": {"points_per_game": 28.5},
                "defense": {"points_allowed_per_game": 20.0},
                "ats_trends": {
                    "wins": 8,
                    "losses": 6,
                    "win_percentage": 0.571,
                    "recent": "3-2",
                    "home": "5-2",
                    "away": "3-4"
                },
                "over_under_trends": {
                    "overs": 7,
                    "unders": 7,
                    "over_percentage": 0.5,
                    "recent_overs": 2,
                    "recent_unders": 3
                }
            },
            "away_team_stats": {
                "team_name": "Chicago Bears",
                "record": {"wins": 7, "losses": 7},
                "offense": {"points_per_game": 22.0},
                "defense": {"points_allowed_per_game": 24.0},
                "ats_trends": {
                    "wins": 6,
                    "losses": 8,
                    "win_percentage": 0.429,
                    "recent": "2-3",
                    "home": "3-4",
                    "away": "3-4"
                },
                "over_under_trends": {
                    "overs": 5,
                    "unders": 9,
                    "over_percentage": 0.357,
                    "recent_overs": 1,
                    "recent_unders": 4
                }
            },
            "weather": {
                "temperature": 35,
                "description": "Partly cloudy",
                "wind_speed": 12
            }
        }
    
    @pytest.mark.asyncio
    async def test_analysis_includes_ats_trends_in_response(self, mock_db, mock_game, mock_markets, mock_matchup_data):
        """Test that ATS trends are included in the final analysis response"""
        generator = AnalysisGeneratorService(mock_db)
        
        # Mock database query for game
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_game
        mock_db.execute.return_value = mock_result
        
        # Mock stats scraper
        with patch.object(generator.stats_scraper, 'get_matchup_data', new_callable=AsyncMock) as mock_get_matchup:
            mock_get_matchup.return_value = mock_matchup_data
            
            # Mock probability engine
            mock_prob_engine = MagicMock()
            mock_prob_engine.calculate_game_win_probability = AsyncMock(return_value={
                "home_win_prob": 0.58,
                "away_win_prob": 0.42,
                "calculation_method": "weighted_model"
            })
            
            with patch('app.services.analysis_generator.get_probability_engine', return_value=mock_prob_engine):
                # Mock OpenAI service's chat completions
                mock_completion = MagicMock()
                mock_completion.choices = [MagicMock()]
                mock_completion.choices[0].message.content = (
                    '{"opening_summary": "Test summary", '
                    '"ats_trends": {"home_team_trend": "Home 8-6 ATS (57.1%)", "away_team_trend": "Away 6-8 ATS (42.9%)", "analysis": "ATS snapshot."}, '
                    '"totals_trends": {"home_team_trend": "Home O/U 7-7 (50.0%)", "away_team_trend": "Away O/U 5-9 (35.7%)", "analysis": "Totals snapshot."}, '
                    '"model_win_probability": {"home_win_prob": 0.58, "away_win_prob": 0.42}}'
                )
                
                with patch.object(generator.openai_service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_openai:
                    mock_openai.return_value = mock_completion
                    
                    # Mock same-game parlays
                    with patch.object(generator, '_generate_same_game_parlays', new_callable=AsyncMock) as mock_parlays:
                        mock_parlays.return_value = []
                        
                        # Mock market query
                        mock_market_result = MagicMock()
                        mock_market_result.scalars.return_value.all.return_value = mock_markets
                        mock_db.execute.return_value = mock_market_result
                        
                        # Execute analysis generation
                        analysis = await generator.generate_game_analysis(
                            game_id=str(mock_game.id),
                            sport="NFL"
                        )
                        
                        # Verify ATS trends are in response
                        assert "ats_trends" in analysis
                        assert "home_team_trend" in analysis["ats_trends"]
                        assert "away_team_trend" in analysis["ats_trends"]
                        assert "analysis" in analysis["ats_trends"]
                        
                        # Verify totals trends are in response
                        assert "totals_trends" in analysis
                        assert "home_team_trend" in analysis["totals_trends"]
                        assert "away_team_trend" in analysis["totals_trends"]
    
    @pytest.mark.asyncio
    async def test_analysis_context_includes_ats_ou_trends(self, mock_db, mock_matchup_data):
        """Test that ATS/O/U trends are included in the AI context"""
        generator = AnalysisGeneratorService(mock_db)
        
        # Build analysis context
        context = generator._build_analysis_context(
            home_team="Green Bay Packers",
            away_team="Chicago Bears",
            league="NFL",
            game_time=datetime.now(),
            matchup_data=mock_matchup_data,
            odds_data={
                "spread_line": -3.5,
                "total_line": 44.5,
                "home_ml": "-175",
                "away_ml": "+155"
            },
            model_probs={
                "home_win_prob": 0.58,
                "away_win_prob": 0.42
            }
        )
        
        # Verify ATS trends are mentioned in context
        assert "ATS" in context or "Against The Spread" in context
        assert "8-6" in context or "6-8" in context  # ATS records
        
        # Verify O/U trends are mentioned in context
        assert "over" in context.lower() or "under" in context.lower()
        assert "7-7" in context or "5-9" in context  # O/U records
    
    @pytest.mark.asyncio
    async def test_analysis_extracts_spread_and_total_lines(self, mock_db, mock_markets):
        """Test that spread and total lines are correctly extracted from markets"""
        generator = AnalysisGeneratorService(mock_db)
        
        spread_line, total_line = generator._extract_lines_from_markets(mock_markets)
        
        assert spread_line is not None
        assert abs(spread_line) == 3.5  # Should extract -3.5 or 3.5
        assert total_line == 44.5
    
    @pytest.mark.asyncio
    async def test_trend_snapshot_builds_correctly(self, mock_db, mock_matchup_data):
        """Test that trend snapshot correctly extracts ATS and O/U data"""
        generator = AnalysisGeneratorService(mock_db)
        
        snapshot = generator._build_trend_snapshot(mock_matchup_data)
        
        # Verify structure
        assert "ats" in snapshot
        assert "over_under" in snapshot
        
        # Verify home team ATS
        assert snapshot["ats"]["home"]["wins"] == 8
        assert snapshot["ats"]["home"]["losses"] == 6
        
        # Verify away team ATS
        assert snapshot["ats"]["away"]["wins"] == 6
        assert snapshot["ats"]["away"]["losses"] == 8
        
        # Verify home team O/U
        assert snapshot["over_under"]["home"]["overs"] == 7
        assert snapshot["over_under"]["home"]["unders"] == 7
        
        # Verify away team O/U
        assert snapshot["over_under"]["away"]["overs"] == 5
        assert snapshot["over_under"]["away"]["unders"] == 9
    
    @pytest.mark.asyncio
    async def test_analysis_handles_missing_ats_ou_data(self, mock_db):
        """Test that analysis handles missing ATS/O/U data gracefully"""
        generator = AnalysisGeneratorService(mock_db)
        
        # Matchup data without ATS/O/U trends
        matchup_data_no_trends = {
            "home_team_stats": {
                "team_name": "Team A",
                "record": {"wins": 5, "losses": 5}
            },
            "away_team_stats": {
                "team_name": "Team B",
                "record": {"wins": 5, "losses": 5}
            }
        }
        
        snapshot = generator._build_trend_snapshot(matchup_data_no_trends)
        
        # Should still return structure, but with None values
        assert "ats" in snapshot
        assert "over_under" in snapshot
        # Values may be None, which is acceptable
    
    @pytest.mark.asyncio
    async def test_analysis_includes_lines_in_response(self, mock_db, mock_game, mock_markets, mock_matchup_data):
        """Test that spread and total lines are included in analysis response"""
        generator = AnalysisGeneratorService(mock_db)
        
        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_game
        mock_db.execute.return_value = mock_result
        
        # Mock stats scraper
        with patch.object(generator.stats_scraper, 'get_matchup_data', new_callable=AsyncMock) as mock_get_matchup:
            mock_get_matchup.return_value = mock_matchup_data
            
            # Mock probability engine
            mock_prob_engine = MagicMock()
            mock_prob_engine.calculate_game_win_probability = AsyncMock(return_value={
                "home_win_prob": 0.58,
                "away_win_prob": 0.42
            })
            
            with patch('app.services.analysis_generator.get_probability_engine', return_value=mock_prob_engine):
                # Mock OpenAI service's chat completions
                mock_completion = MagicMock()
                mock_completion.choices = [MagicMock()]
                mock_completion.choices[0].message.content = '{"opening_summary": "Test", "model_win_probability": {"home_win_prob": 0.58, "away_win_prob": 0.42}}'
                
                with patch.object(generator.openai_service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_openai:
                    mock_openai.return_value = mock_completion
                    
                    # Mock same-game parlays
                    with patch.object(generator, '_generate_same_game_parlays', new_callable=AsyncMock):
                        # Mock market query
                        mock_market_result = MagicMock()
                        mock_market_result.scalars.return_value.all.return_value = mock_markets
                        mock_db.execute.return_value = mock_market_result
                        
                        analysis = await generator.generate_game_analysis(
                            game_id=str(mock_game.id),
                            sport="NFL"
                        )
                        
                        # Verify lines are included
                        assert "lines" in analysis
                        assert "spread" in analysis["lines"]
                        assert "total" in analysis["lines"]
                        assert analysis["lines"]["spread"] is not None
                        assert analysis["lines"]["total"] == 44.5


class TestAnalysisIntegration:
    """Integration tests for analysis generation with real data flow"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        db = AsyncMock()
        db.execute = AsyncMock()
        return db
    
    @pytest.mark.asyncio
    async def test_full_analysis_flow_structure(self, mock_db):
        """Test that full analysis flow returns all required fields"""
        generator = AnalysisGeneratorService(mock_db)
        
        # Create minimal mocks for full flow
        mock_game = MagicMock()
        mock_game.id = uuid.uuid4()
        mock_game.sport = "NFL"
        mock_game.home_team = "Team A"
        mock_game.away_team = "Team B"
        mock_game.start_time = datetime.now()
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_game
        mock_db.execute.return_value = mock_result
        
        # Mock all dependencies
        with patch.object(generator.stats_scraper, 'get_matchup_data', new_callable=AsyncMock) as mock_matchup:
            mock_matchup.return_value = {
                "home_team_stats": {"ats_trends": {"wins": 5}, "over_under_trends": {"overs": 5}},
                "away_team_stats": {"ats_trends": {"wins": 5}, "over_under_trends": {"overs": 5}}
            }
            
            mock_prob_engine = MagicMock()
            mock_prob_engine.calculate_game_win_probability = AsyncMock(return_value={
                "home_win_prob": 0.55,
                "away_win_prob": 0.45
            })
            
            with patch('app.services.analysis_generator.get_probability_engine', return_value=mock_prob_engine):
                # Mock OpenAI service's chat completions
                mock_completion = MagicMock()
                mock_completion.choices = [MagicMock()]
                mock_completion.choices[0].message.content = '{"opening_summary": "Test summary", "model_win_probability": {"home_win_prob": 0.55, "away_win_prob": 0.45}}'
                
                with patch.object(generator.openai_service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_openai:
                    mock_openai.return_value = mock_completion
                    
                    with patch.object(generator, '_generate_same_game_parlays', new_callable=AsyncMock):
                        mock_market_result = MagicMock()
                        mock_market_result.scalars.return_value.all.return_value = []
                        mock_db.execute.return_value = mock_market_result
                        
                        analysis = await generator.generate_game_analysis(
                            game_id=str(mock_game.id),
                            sport="NFL"
                        )
                        
                        # Verify all required fields are present
                        required_fields = [
                            "opening_summary",
                            "ats_trends",
                            "totals_trends",
                            "model_win_probability",
                            "lines",
                            "generated_at"
                        ]
                        
                        for field in required_fields:
                            assert field in analysis, f"Missing required field: {field}"

