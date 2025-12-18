import pytest
from pydantic import ValidationError

from app.schemas.parlay import CustomParlayRequest


def _leg(i: int) -> dict:
    # game_id is treated as a string in the schema; UUID validation happens in the route
    return {"game_id": f"game-{i}", "pick": "home", "market_type": "h2h"}


def test_custom_parlay_request_allows_1_leg():
    req = CustomParlayRequest(legs=[_leg(1)])
    assert len(req.legs) == 1


def test_custom_parlay_request_allows_20_legs():
    req = CustomParlayRequest(legs=[_leg(i) for i in range(20)])
    assert len(req.legs) == 20


def test_custom_parlay_request_rejects_21_legs():
    with pytest.raises(ValidationError):
        CustomParlayRequest(legs=[_leg(i) for i in range(21)])


