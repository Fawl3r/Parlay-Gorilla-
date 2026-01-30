from app.services.analysis.analysis_contract import is_core_ready


def _base_content() -> dict:
    return {
        "opening_summary": "Quick preview for Los Angeles Rams @ Seattle Seahawks.",
        "ats_trends": {
            "home_team_trend": "Seattle Seahawks is 1-1-0 ATS (50.0% cover rate). Recent: 1-1 ATS.",
            "away_team_trend": "Los Angeles Rams is 1-0-0 ATS (100.0% cover rate). Recent: 2-0 ATS.",
            "analysis": "Los Angeles Rams has been the more reliable ATS side so far.",
        },
        "totals_trends": {
            "home_team_trend": "Seattle Seahawks totals have gone Over 1 times and Under 1 times (50.0% over rate).",
            "away_team_trend": "Los Angeles Rams totals have gone Over 1 times and Under 0 times (100.0% over rate).",
            "analysis": "Combined O/U tendencies point slightly toward the Over.",
        },
        "ai_spread_pick": {"pick": "Los Angeles Rams +1.5", "confidence": 55, "rationale": "Edge vs market."},
        "ai_total_pick": {"pick": "Over 49.0", "confidence": 60, "rationale": "Pace + efficiency."},
        "best_bets": [{"pick": "Los Angeles Rams +1.5", "confidence": 55, "rationale": "Edge."}],
        "model_win_probability": {"home_win_prob": 0.5168, "away_win_prob": 0.4832, "ai_confidence": 30.0},
        "confidence_breakdown": {
            "market_agreement": 15.0,
            "statistical_edge": 10.0,
            "situational_edge": 5.0,
            "data_quality": 8.0,
            "confidence_total": 38.0,
            "explanation": "Moderate confidence based on market and stats.",
            "trend": None,
        },
        "full_article": "",
    }


def test_is_core_ready_valid_content_is_true():
    assert is_core_ready(_base_content()) is True


def test_is_core_ready_impossible_percentage_is_false():
    content = _base_content()
    content["ats_trends"]["home_team_trend"] = "Seattle Seahawks is 1-0-0 ATS (10000.0% cover rate). Recent: 1-0 ATS."
    assert is_core_ready(content) is False


def test_is_core_ready_mismatched_availability_is_false():
    content = _base_content()
    content["ats_trends"]["away_team_trend"] = "ATS data is not currently available for Los Angeles Rams."
    assert is_core_ready(content) is False


def test_is_core_ready_both_sides_missing_is_still_true():
    content = _base_content()
    content["ats_trends"] = {
        "home_team_trend": "ATS data is not currently available for Seattle Seahawks.",
        "away_team_trend": "ATS data is not currently available for Los Angeles Rams.",
        "analysis": "ATS trend data is limited for this matchup. We’re leaning more on the model and current prices.",
    }
    content["totals_trends"] = {
        "home_team_trend": "Over/under data is not currently available for Seattle Seahawks.",
        "away_team_trend": "Over/under data is not currently available for Los Angeles Rams.",
        "analysis": "Totals trend data is limited for this matchup. We’re leaning more on pace, efficiency, and the posted number.",
    }
    assert is_core_ready(content) is True


def test_is_core_ready_missing_confidence_breakdown_is_false():
    """Legacy payloads without confidence_breakdown are not core-ready (so they get upgraded)."""
    content = _base_content()
    del content["confidence_breakdown"]
    assert is_core_ready(content) is False


def test_is_core_ready_confidence_breakdown_empty_dict_is_false():
    """confidence_breakdown must be a dict with at least confidence_total."""
    content = _base_content()
    content["confidence_breakdown"] = {}
    assert is_core_ready(content) is False


def test_is_core_ready_confidence_breakdown_without_total_is_false():
    """confidence_breakdown without confidence_total is invalid (e.g. malformed payload)."""
    content = _base_content()
    content["confidence_breakdown"] = {"market_agreement": 10.0}
    assert is_core_ready(content) is False
