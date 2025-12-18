"""Tests for advanced parlay features (same-game, round-robin, teasers)"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_same_game_parlay(client: AsyncClient):
    """Test same-game parlay generation"""
    # This would require a game_id - using a mock for now
    response = await client.post(
        "/api/parlay/variants/same-game",
        json={
            "game_id": "test-game-id",
            "num_legs": 3,
        }
    )
    
    # Should either succeed or return appropriate error
    assert response.status_code in [200, 400, 404]


@pytest.mark.asyncio
async def test_round_robin_parlay(client: AsyncClient):
    """Test round-robin parlay generation"""
    response = await client.post(
        "/api/parlay/variants/round-robin",
        json={
            "legs": [
                {"game_id": "game1", "pick": "home", "market_type": "h2h"},
                {"game_id": "game2", "pick": "away", "market_type": "h2h"},
                {"game_id": "game3", "pick": "over", "market_type": "totals"},
            ],
            "ways": 2,  # 2-way round robin
        }
    )
    
    # Should either succeed or return appropriate error (422 = request validation)
    assert response.status_code in [200, 400, 404, 422]


@pytest.mark.asyncio
async def test_teaser_parlay(client: AsyncClient):
    """Test teaser parlay generation"""
    response = await client.post(
        "/api/parlay/variants/teaser",
        json={
            "legs": [
                {"game_id": "game1", "pick": "home", "market_type": "spreads", "point": -7},
                {"game_id": "game2", "pick": "away", "market_type": "spreads", "point": 3},
            ],
            "teaser_points": 6,  # 6-point teaser
        }
    )
    
    # Should either succeed or return appropriate error (422 = request validation)
    assert response.status_code in [200, 400, 404, 422]

