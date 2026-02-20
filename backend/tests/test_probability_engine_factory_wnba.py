from unittest.mock import MagicMock

from app.services.probability_engine_impl.engines import WNBAProbabilityEngine
from app.services.probability_engine_impl.factory import get_probability_engine


def test_factory_returns_wnba_engine_for_slug():
    engine = get_probability_engine(MagicMock(), "wnba")
    assert isinstance(engine, WNBAProbabilityEngine)
    assert getattr(engine.injury_fetcher, "sport", "") == "wnba"


def test_factory_returns_wnba_engine_for_odds_key():
    engine = get_probability_engine(MagicMock(), "basketball_wnba")
    assert isinstance(engine, WNBAProbabilityEngine)
    assert getattr(engine.injury_fetcher, "sport", "") == "wnba"
