import pytest
from pydantic import ValidationError

from app.schemas.parlay import ParlayRequest


def test_parlay_request_allows_postseason_weeks():
    # Postseason weeks are represented as weeks 19-22 (Wild Card -> Super Bowl).
    ParlayRequest(num_legs=5, risk_profile="balanced", week=19)
    ParlayRequest(num_legs=5, risk_profile="balanced", week=22)


def test_parlay_request_rejects_week_over_22():
    with pytest.raises(ValidationError):
        ParlayRequest(num_legs=5, risk_profile="balanced", week=23)


