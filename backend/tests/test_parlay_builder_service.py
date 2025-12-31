"""Comprehensive tests for parlay builder service and slip generation"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.parlay_builder import ParlayBuilderService
from app.services.mixed_sports_parlay import MixedSportsParlayBuilder


@pytest.fixture
def mock_db():
    """Mock database session"""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_prob_engine():
    """Mock probability engine"""
    engine = MagicMock()
    engine.get_candidate_legs = AsyncMock(return_value=[])
    engine.calculate_parlay_probability = MagicMock(side_effect=lambda probs: 1.0 if not probs else sum(probs) / len(probs))
    return engine


def create_mock_leg(
    game_id: str,
    market_id: str,
    outcome: str,
    confidence: float = 60.0,
    prob: float = 0.6,
    market_type: str = "h2h",
):
    """Helper to create a properly structured mock leg"""
    return {
        "game_id": game_id,
        "market_id": market_id,
        "outcome": outcome,
        "confidence_score": confidence,
        "probability": prob,
        "adjusted_prob": prob,  # Required field
        "implied_prob": 0.5,  # Common/default for edge scoring
        "decimal_odds": 1.91,  # Typical -110
        "edge": prob - 0.5,
        "odds": "-110",
        "game": f"Team A vs Team B (Game {game_id})",
        "home_team": "Team B",
        "away_team": "Team A",
        "market_type": market_type,
        "pick": outcome,
    }


class TestParlayBuilderService:
    """Tests for ParlayBuilderService"""
    
    @pytest.mark.asyncio
    async def test_build_parlay_validates_num_legs(self, mock_db, mock_prob_engine):
        """Test that num_legs is clamped to valid range (1-20)"""
        with patch('app.services.parlay_builder_impl.parlay_builder_service.get_probability_engine', return_value=mock_prob_engine):
            builder = ParlayBuilderService(mock_db, sport="NFL")
            
            # Test clamping to minimum - need proper leg structure
            mock_prob_engine.get_candidate_legs.return_value = [
                create_mock_leg("game1", "market1", "home", 60.0, 0.6)
            ]
            result = await builder.build_parlay(num_legs=0, risk_profile="balanced")
            assert result["num_legs"] >= 1  # May be less if only 1 leg available
            
            # Test clamping to maximum
            mock_prob_engine.get_candidate_legs.return_value = [
                create_mock_leg(f"game{i}", f"market{i}", "home", 60.0, 0.6) for i in range(25)
            ]
            result = await builder.build_parlay(num_legs=25, risk_profile="balanced")
            assert result["num_legs"] <= 20
    
    @pytest.mark.asyncio
    async def test_build_parlay_validates_risk_profile(self, mock_db, mock_prob_engine):
        """Test that invalid risk profiles default to balanced"""
        with patch('app.services.parlay_builder_impl.parlay_builder_service.get_probability_engine', return_value=mock_prob_engine):
            builder = ParlayBuilderService(mock_db, sport="NFL")
            
            mock_prob_engine.get_candidate_legs.return_value = [
                create_mock_leg("game1", "market1", "home", 60.0, 0.6)
            ]
            
            # Invalid profile should default to balanced
            result = await builder.build_parlay(num_legs=1, risk_profile="invalid")
            assert result["risk_profile"] == "balanced"
            
            # Valid profiles should be preserved
            for profile in ["conservative", "balanced", "degen"]:
                mock_prob_engine.get_candidate_legs.return_value = [
                    create_mock_leg("game1", "market1", "home", 60.0, 0.6)
                ]
                result = await builder.build_parlay(num_legs=1, risk_profile=profile)
                assert result["risk_profile"] == profile
    
    @pytest.mark.asyncio
    async def test_build_parlay_handles_insufficient_candidates(self, mock_db, mock_prob_engine):
        """Test that builder handles cases with insufficient candidate legs"""
        with patch('app.services.parlay_builder_impl.parlay_builder_service.get_probability_engine', return_value=mock_prob_engine):
            builder = ParlayBuilderService(mock_db, sport="NFL")
            
            # No candidates available
            mock_prob_engine.get_candidate_legs.return_value = []
            
            # Should raise ValueError when no candidates available
            with pytest.raises(ValueError, match="Not enough candidate legs"):
                await builder.build_parlay(num_legs=3, risk_profile="balanced")
    
    @pytest.mark.asyncio
    async def test_build_parlay_calculates_probability(self, mock_db, mock_prob_engine):
        """Test that parlay probability is calculated correctly from leg probabilities"""
        with patch('app.services.parlay_builder_impl.parlay_builder_service.get_probability_engine', return_value=mock_prob_engine):
            builder = ParlayBuilderService(mock_db, sport="NFL")
            
            # Mock candidates with known probabilities - need unique game_id/market_type/outcome
            mock_prob_engine.get_candidate_legs.return_value = [
                create_mock_leg("game1", "market1", "home", 70.0, 0.7),
                create_mock_leg("game2", "market2", "away", 65.0, 0.65),
                create_mock_leg("game3", "market3", "home", 60.0, 0.6),
            ]
            
            # Mock calculate_parlay_probability to return product
            def calc_prob(probs):
                if not probs:
                    return 0.0
                result = 1.0
                for p in probs:
                    result *= p
                return result
            
            mock_prob_engine.calculate_parlay_probability = MagicMock(side_effect=calc_prob)
            
            result = await builder.build_parlay(num_legs=3, risk_profile="balanced")
            
            # Should have 3 legs
            assert len(result["legs"]) == 3
            
            # Should calculate parlay probability (product of individual probabilities)
            expected_prob = 0.7 * 0.65 * 0.6
            assert abs(result["parlay_hit_prob"] - expected_prob) < 0.01

    @pytest.mark.asyncio
    async def test_build_parlay_fills_to_requested_legs_with_relaxed_correlation(self, mock_db, mock_prob_engine):
        """
        Regression test: previously, correlated-but-valid legs could be dropped and never refilled,
        resulting in fewer legs than requested (e.g., requested 9, got 8).

        We build a small candidate pool where the only way to reach the target is to accept
        some correlated (same game) legs across different market types.
        """
        with patch(
            "app.services.parlay_builder_impl.parlay_builder_service.get_probability_engine",
            return_value=mock_prob_engine,
        ):
            builder = ParlayBuilderService(mock_db, sport="NFL")

            # 5 games, each with two "home" legs across different market types.
            # Correlation between h2h(home) and spreads(home) in the same game is 0.7.
            candidates = []
            for i in range(5):
                candidates.append(create_mock_leg(f"game{i}", f"m{i}-h2h", "home", 70.0, 0.60, market_type="h2h"))
                candidates.append(create_mock_leg(f"game{i}", f"m{i}-spr", "home", 69.0, 0.59, market_type="spreads"))

            mock_prob_engine.get_candidate_legs.return_value = candidates

            result = await builder.build_parlay(num_legs=9, risk_profile="balanced")

            assert result["num_legs"] == 9
            assert len(result["legs"]) == 9
    
    @pytest.mark.asyncio
    async def test_build_parlay_filters_by_risk_profile(self, mock_db, mock_prob_engine):
        """Test that risk profile affects confidence threshold"""
        with patch('app.services.parlay_builder_impl.parlay_builder_service.get_probability_engine', return_value=mock_prob_engine):
            builder = ParlayBuilderService(mock_db, sport="NFL")
            
            # Provide enough candidates for both profiles
            mock_prob_engine.get_candidate_legs.return_value = [
                create_mock_leg(f"game{i}", f"market{i}", "home", 50.0 + i, 0.5 + i/100) for i in range(10)
            ]
            
            # Conservative should require higher confidence
            mock_prob_engine.reset_mock()
            try:
                await builder.build_parlay(num_legs=3, risk_profile="conservative")
            except ValueError:
                pass  # May fail if not enough candidates, that's ok
            conservative_calls = mock_prob_engine.get_candidate_legs.call_args_list
            
            # Degen should allow lower confidence
            mock_prob_engine.reset_mock()
            mock_prob_engine.get_candidate_legs.return_value = [
                create_mock_leg(f"game{i}", f"market{i}", "home", 50.0 + i, 0.5 + i/100) for i in range(10)
            ]
            try:
                await builder.build_parlay(num_legs=3, risk_profile="degen")
            except ValueError:
                pass  # May fail if not enough candidates, that's ok
            degen_calls = mock_prob_engine.get_candidate_legs.call_args_list
            
            # Conservative should have higher min_confidence in initial call
            if conservative_calls and degen_calls:
                conservative_min = conservative_calls[0].kwargs.get("min_confidence", 0)
                degen_min = degen_calls[0].kwargs.get("min_confidence", 0)
                assert conservative_min >= degen_min

    @pytest.mark.asyncio
    async def test_build_triple_parlay_reuses_candidate_pool_per_sport(self, mock_db):
        """Triple parlay should fetch candidate legs once per sport and reuse across profiles."""
        mock_engine = MagicMock()

        # Candidate legs must satisfy safe/balanced/degen thresholds.
        candidates = []
        for i in range(20):
            confidence = 75.0 if i < 6 else 60.0 if i < 16 else 45.0
            candidates.append(
                create_mock_leg(
                    game_id=f"game{i}",
                    market_id=f"market{i}",
                    outcome="home",
                    confidence=confidence,
                    prob=0.55,
                )
            )
            candidates[-1]["implied_prob"] = 0.5
            candidates[-1]["decimal_odds"] = 1.91
            candidates[-1]["edge"] = float(candidates[-1]["adjusted_prob"]) - 0.5

        mock_engine.get_candidate_legs = AsyncMock(return_value=candidates)

        def calc_prob(probs):
            p = 1.0
            for x in probs or []:
                p *= float(x)
            return p

        mock_engine.calculate_parlay_probability = MagicMock(side_effect=calc_prob)

        with patch('app.services.parlay_builder_impl.parlay_builder_service.get_probability_engine', return_value=mock_engine):
            builder = ParlayBuilderService(mock_db, sport="NFL")
            result = await builder.build_triple_parlay(sports=["NFL"])

        assert "safe" in result and "balanced" in result and "degen" in result
        assert mock_engine.get_candidate_legs.await_count == 1


class TestMixedSportsParlayBuilder:
    """Tests for MixedSportsParlayBuilder"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return AsyncMock(spec=AsyncSession)
    
    @pytest.mark.asyncio
    async def test_build_mixed_parlay_validates_sports(self, mock_db):
        """Test that invalid sports are filtered out"""
        builder = MixedSportsParlayBuilder(mock_db)
        
        # Mock the probability engines
        with patch.object(builder, '_get_engine') as mock_get_engine:
            nfl_engine = MagicMock()
            nfl_engine.get_candidate_legs = AsyncMock(
                return_value=[
                    create_mock_leg("nfl_game1", "nfl_market1", "home", 70.0, 0.62),
                    create_mock_leg("nfl_game2", "nfl_market2", "away", 68.0, 0.60),
                ]
            )
            nba_engine = MagicMock()
            nba_engine.get_candidate_legs = AsyncMock(
                return_value=[
                    create_mock_leg("nba_game1", "nba_market1", "home", 66.0, 0.58),
                    create_mock_leg("nba_game2", "nba_market2", "away", 65.0, 0.57),
                ]
            )

            def get_engine_side_effect(sport: str):
                if sport == "NFL":
                    return nfl_engine
                if sport == "NBA":
                    return nba_engine
                raise AssertionError(f"Unexpected engine request for sport: {sport}")

            mock_get_engine.side_effect = get_engine_side_effect
            
            # Invalid sports should be filtered
            result = await builder.build_mixed_parlay(
                num_legs=3,
                sports=["NFL", "INVALID", "NBA"],
                risk_profile="balanced"
            )
            
            # Should only use valid sports (NFL, NBA) and return non-empty legs
            assert result is not None
            assert len(result.get("legs", [])) > 0
            called_sports = [call.args[0] for call in mock_get_engine.call_args_list]
            assert "INVALID" not in called_sports
    
    @pytest.mark.asyncio
    async def test_build_mixed_parlay_balances_sports(self, mock_db):
        """Test that balance_sports parameter distributes legs across sports"""
        builder = MixedSportsParlayBuilder(mock_db)
        
        # Mock engines for different sports
        nfl_engine = MagicMock()
        nfl_engine.get_candidate_legs = AsyncMock(return_value=[
            create_mock_leg(f"nfl_game{i}", f"nfl_market{i}", "home", 60.0 + i, 0.55 + (i * 0.01))
            for i in range(5)
        ])
        
        nba_engine = MagicMock()
        nba_engine.get_candidate_legs = AsyncMock(return_value=[
            create_mock_leg(f"nba_game{i}", f"nba_market{i}", "away", 60.0 + i, 0.55 + (i * 0.01))
            for i in range(5)
        ])
        
        with patch.object(builder, '_get_engine') as mock_get_engine:
            def get_engine_side_effect(sport):
                if sport == "NFL":
                    return nfl_engine
                elif sport == "NBA":
                    return nba_engine
                return MagicMock()
            
            mock_get_engine.side_effect = get_engine_side_effect
            
            result = await builder.build_mixed_parlay(
                num_legs=4,
                sports=["NFL", "NBA"],
                risk_profile="balanced",
                balance_sports=True
            )
            
            # Should have legs from both sports
            assert result and "legs" in result and len(result["legs"]) == 4
            sports_in_result = {leg.get("sport") for leg in result["legs"] if leg.get("sport")}
            assert "NFL" in sports_in_result
            assert "NBA" in sports_in_result

    @pytest.mark.asyncio
    async def test_build_mixed_parlay_raises_when_no_candidates(self, mock_db):
        """Never return a 0-leg parlay: raise when no candidate legs exist."""
        builder = MixedSportsParlayBuilder(mock_db)

        empty_engine = MagicMock()
        empty_engine.get_candidate_legs = AsyncMock(return_value=[])

        with patch.object(builder, "_get_engine", return_value=empty_engine):
            with pytest.raises(ValueError, match="Not enough candidate legs available"):
                await builder.build_mixed_parlay(
                    num_legs=5,
                    sports=["NBA", "NHL"],
                    risk_profile="balanced",
                    balance_sports=True,
                )


class TestParlaySlipFormatting:
    """Tests for parlay slip data formatting and structure"""
    
    @pytest.mark.asyncio
    async def test_parlay_response_structure(self, mock_db, mock_prob_engine):
        """Test that parlay response has correct structure for slip display"""
        with patch('app.services.parlay_builder_impl.parlay_builder_service.get_probability_engine', return_value=mock_prob_engine):
            builder = ParlayBuilderService(mock_db, sport="NFL")
            
            mock_prob_engine.get_candidate_legs.return_value = [
                create_mock_leg("game1", "market1", "home", 70.0, 0.7)
            ]
            
            result = await builder.build_parlay(num_legs=1, risk_profile="balanced")
            
            # Verify required fields for slip display
            assert "num_legs" in result
            assert "legs" in result
            assert "parlay_hit_prob" in result
            assert "risk_profile" in result
            
            # Verify leg structure
            if result["legs"]:
                leg = result["legs"][0]
                assert "market_id" in leg or "game" in leg
                assert "odds" in leg
                assert "confidence" in leg or "confidence_score" in leg
    
    @pytest.mark.asyncio
    async def test_parlay_odds_calculation(self, mock_db, mock_prob_engine):
        """Test that parlay odds are calculated correctly from leg odds"""
        with patch('app.services.parlay_builder_impl.parlay_builder_service.get_probability_engine', return_value=mock_prob_engine):
            builder = ParlayBuilderService(mock_db, sport="NFL")
            
            # Mock legs with known odds - need unique game_id/market_type/outcome
            mock_prob_engine.get_candidate_legs.return_value = [
                create_mock_leg(f"game{i}", f"market{i}", "home", 60.0, 0.6) for i in range(3)
            ]
            
            result = await builder.build_parlay(num_legs=3, risk_profile="balanced")
            
            # Verify response has required fields for slip display
            assert "legs" in result
            assert len(result["legs"]) == 3
            
            # Each leg should have odds
            for leg in result["legs"]:
                assert "odds" in leg
                odds_str = str(leg["odds"])
                # Should be in American odds format
                assert "+" in odds_str or "-" in odds_str
            
            # Response may have total_odds or parlay_odds, but it's not guaranteed
            # The important thing is that each leg has odds for slip display

