from app.api.routes.parlay import _normalize_sport_code, _normalize_sports


def test_normalize_sport_code_maps_wnba_aliases():
    assert _normalize_sport_code("wnba") == "WNBA"
    assert _normalize_sport_code("basketball_wnba") == "WNBA"


def test_normalize_sports_dedupes_and_defaults():
    assert _normalize_sports(["WNBA", "basketball_wnba", "nfl"]) == ["WNBA", "NFL"]
    assert _normalize_sports(None) == ["NFL"]
