import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_upset_finder_filters_and_ranks_candidates():
    """
    Upset Finder should:
    - consider only underdogs (implied_prob <= 0.50 and plus-money odds)
    - enforce min_edge and positive EV
    - return results sorted by EV desc
    """
    from app.services.upset_finder import UpsetFinderService

    mock_db = AsyncMock()
    mock_engine = MagicMock()
    mock_engine.get_candidate_legs = AsyncMock(
        return_value=[
            # Valid upset (away underdog)
            {
                "outcome": "away",
                "home_team": "Home A",
                "away_team": "Away A",
                "market_type": "h2h",
                "implied_prob": 0.45,
                "adjusted_prob": 0.56,
                "odds": +140,
                "confidence_score": 62.0,
                "game_id": "game-a",
            },
            # Higher EV valid upset (home underdog)
            {
                "outcome": "home",
                "home_team": "Home B",
                "away_team": "Away B",
                "market_type": "h2h",
                "implied_prob": 0.40,
                "adjusted_prob": 0.55,
                "odds": +180,
                "confidence_score": 58.0,
                "game_id": "game-b",
            },
            # Not an underdog (implied > 50%)
            {
                "outcome": "home",
                "home_team": "Home C",
                "away_team": "Away C",
                "market_type": "h2h",
                "implied_prob": 0.62,
                "adjusted_prob": 0.70,
                "odds": -165,
                "confidence_score": 70.0,
                "game_id": "game-c",
            },
            # Edge too small
            {
                "outcome": "away",
                "home_team": "Home D",
                "away_team": "Away D",
                "market_type": "h2h",
                "implied_prob": 0.49,
                "adjusted_prob": 0.50,
                "odds": +105,
                "confidence_score": 55.0,
                "game_id": "game-d",
            },
        ]
    )

    with patch("app.services.upset_finder.get_probability_engine", return_value=mock_engine):
        service = UpsetFinderService(mock_db, sport="NFL")
        upsets = await service.find_upsets(min_edge=0.03, max_results=10)

    assert len(upsets) == 2
    # Sorted by EV desc => candidate with +180 and 55% should be first.
    assert upsets[0].game_id == "game-b"
    assert upsets[1].game_id == "game-a"


@pytest.mark.asyncio
async def test_upset_finder_risk_tier_filter():
    """Risk tier filter should return only candidates matching the requested tier."""
    from app.services.upset_finder import UpsetFinderService

    mock_db = AsyncMock()
    mock_engine = MagicMock()
    mock_engine.get_candidate_legs = AsyncMock(
        return_value=[
            {
                "outcome": "away",
                "home_team": "Home A",
                "away_team": "Away A",
                "market_type": "h2h",
                "implied_prob": 0.48,
                "adjusted_prob": 0.58,
                "odds": +120,
                "confidence_score": 60.0,
                "game_id": "game-a",
            },
            {
                "outcome": "away",
                "home_team": "Home B",
                "away_team": "Away B",
                "market_type": "h2h",
                "implied_prob": 0.30,
                "adjusted_prob": 0.40,
                "odds": +350,
                "confidence_score": 45.0,
                "game_id": "game-b",
            },
        ]
    )

    with patch("app.services.upset_finder.get_probability_engine", return_value=mock_engine):
        service = UpsetFinderService(mock_db, sport="NFL")
        low = await service.find_upsets(min_edge=0.03, max_results=10, risk_tier="low")
        high = await service.find_upsets(min_edge=0.03, max_results=10, risk_tier="high")

    assert all(u.risk_tier == "low" for u in low)
    assert all(u.risk_tier == "high" for u in high)




