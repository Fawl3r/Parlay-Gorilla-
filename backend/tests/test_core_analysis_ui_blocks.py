import pytest

from app.services.analysis.core_analysis_ui_blocks import CoreAnalysisUiBlocksBuilder


def _flatten_strings(value):
    out = []
    if isinstance(value, str):
        out.append(value)
    elif isinstance(value, dict):
        for v in value.values():
            out.extend(_flatten_strings(v))
    elif isinstance(value, list):
        for item in value:
            out.extend(_flatten_strings(item))
    return out


def test_ui_blocks_shape_and_guardrails():
    builder = CoreAnalysisUiBlocksBuilder.for_sport("NFL")
    blocks = builder.build(
        home_team="Atlanta Falcons",
        away_team="Los Angeles Rams",
        model_probs={
            "home_win_prob": 0.28,
            "away_win_prob": 0.72,
            "ai_confidence": 72,
            "calculation_method": "unknown",
        },
        opening_summary="The Rams have the cleaner matchup on both sides of the ball. Keep an eye on late-game variance.",
        spread_pick={"pick": "Rams -3", "confidence": 65, "rationale": "Better matchup edge overall."},
        total_pick={"pick": "Under 44.5", "confidence": 52, "rationale": "Both teams slow it down."},
        offensive_edges={"key_matchup": "Rams pace advantage", "away_advantage": "Rams create cleaner looks."},
        defensive_edges={"key_matchup": "Falcons protection concerns", "home_advantage": "Falcons can force punts."},
        ats_trends={"analysis": "One side has been more reliable lately."},
        totals_trends={"analysis": "Totals lean slightly Under recently."},
        weather_considerations="",
    )

    assert isinstance(blocks, dict)
    assert "ui_quick_take" in blocks
    assert "ui_key_drivers" in blocks
    assert "ui_bet_options" in blocks
    assert "ui_matchup_cards" in blocks
    assert "ui_trends" in blocks

    qt = blocks["ui_quick_take"]
    assert isinstance(qt, dict)
    assert qt.get("favored_team") in {"Los Angeles Rams", "Atlanta Falcons"}
    assert isinstance(qt.get("confidence_percent"), int)
    assert qt.get("risk_level") in {"Low", "Medium", "High"}
    assert qt.get("confidence_level") in {"Low", "Medium", "High"}

    kd = blocks["ui_key_drivers"]
    assert isinstance(kd, dict)
    assert isinstance(kd.get("positives"), list)
    assert isinstance(kd.get("risks"), list)
    assert len(kd.get("risks") or []) >= 1

    bet_opts = blocks["ui_bet_options"]
    assert isinstance(bet_opts, list)
    assert any(o.get("id") == "moneyline" for o in bet_opts if isinstance(o, dict))

    # Guardrails: no technical jargon
    joined = " ".join(_flatten_strings(blocks)).lower()
    assert "model confidence" not in joined
    assert "expected value" not in joined
    assert "variance" not in joined


def test_ui_blocks_limited_data_note():
    builder = CoreAnalysisUiBlocksBuilder.for_sport("NBA")
    blocks = builder.build(
        home_team="Home",
        away_team="Away",
        model_probs={
            "home_win_prob": 0.52,
            "away_win_prob": 0.48,
            "ai_confidence": 15,
            "calculation_method": "fallback",
        },
        opening_summary="This matchup has limited historical data. The AI adjusted confidence accordingly.",
        spread_pick={"pick": "", "confidence": 0, "rationale": ""},
        total_pick={"pick": "", "confidence": 0, "rationale": ""},
        offensive_edges={},
        defensive_edges={},
        ats_trends={},
        totals_trends={},
        weather_considerations="",
    )

    qt = blocks.get("ui_quick_take") or {}
    assert isinstance(qt, dict)
    assert isinstance(qt.get("limited_data_note"), str)
    assert "limited" in str(qt.get("limited_data_note")).lower()


