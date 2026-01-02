import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.parlay_builder import ParlayBuilderService


def _mock_leg(game_id: str = "g1", market_id: str = "m1", outcome: str = "home") -> dict:
    # Minimal structure required by ParlayBuilderService and selection logic.
    prob = 0.6
    implied = 0.5
    return {
        "game_id": game_id,
        "market_id": market_id,
        "outcome": outcome,
        "confidence_score": 60.0,
        "adjusted_prob": prob,
        "implied_prob": implied,
        "decimal_odds": 1.91,
        "edge": prob - implied,
        "odds": "-110",
        "game": "Team A @ Team B",
        "home_team": "Team B",
        "away_team": "Team A",
        "market_type": "h2h",
    }


@pytest.mark.asyncio
async def test_build_parlay_retries_candidates_after_odds_warmup():
    """
    Ensure parlay generation retries candidate legs after a successful odds warmup.

    This prevents 503s on cold starts where the odds sync hasn't populated the DB yet.
    """
    mock_db = AsyncMock(spec=AsyncSession)
    mock_engine = MagicMock()
    mock_engine.get_candidate_legs = AsyncMock(side_effect=[[], [_mock_leg()]])

    with patch(
        "app.services.parlay_builder_impl.parlay_builder_service.get_probability_engine",
        return_value=mock_engine,
    ), patch(
        "app.services.parlay_builder_impl.parlay_builder_service.OddsWarmupService.warm_sport",
        new=AsyncMock(return_value=True),
    ):
        builder = ParlayBuilderService(mock_db, sport="NFL")
        result = await builder.build_parlay(num_legs=1, risk_profile="balanced")

    assert result["num_legs"] == 1
    assert len(result["legs"]) == 1


