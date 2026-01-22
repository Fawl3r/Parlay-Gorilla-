"""Test prop recommendations builder."""

import pytest
from app.services.analysis.builders.prop_recommendations_builder import PropRecommendationsBuilder


def test_prop_recommendations_builder_no_props():
    """Test builder returns None when no props available."""
    props_snapshot = {"props": []}
    
    result = PropRecommendationsBuilder.build(
        props_snapshot=props_snapshot,
        game=None,  # Not needed for this test
    )
    
    assert result is None


def test_prop_recommendations_builder_with_props():
    """Test builder produces recommendations from props."""
    props_snapshot = {
        "props": [
            {
                "market_key": "player_points",
                "player_name": "LeBron James",
                "line": 27.5,
                "over_price": "-110",
                "under_price": "-110",
                "best_book_over": "fanduel",
                "best_book_under": "draftkings",
            },
            {
                "market_key": "player_assists",
                "player_name": "Stephen Curry",
                "line": 8.5,
                "over_price": "+105",
                "under_price": "-125",
                "best_book_over": "fanduel",
                "best_book_under": "draftkings",
            },
        ]
    }
    
    class MockGame:
        sport = "NBA"
    
    result = PropRecommendationsBuilder.build(
        props_snapshot=props_snapshot,
        game=MockGame(),
    )
    
    assert result is not None
    assert "top_props" in result
    assert "notes" in result
    assert isinstance(result["top_props"], list)
    assert len(result["top_props"]) > 0
    
    # Check structure of first prop
    first_prop = result["top_props"][0]
    assert "market" in first_prop
    assert "player" in first_prop
    assert "pick" in first_prop
    assert "confidence" in first_prop
    assert "why" in first_prop
    assert "best_odds" in first_prop
    assert "book" in first_prop["best_odds"]
    assert "price" in first_prop["best_odds"]
