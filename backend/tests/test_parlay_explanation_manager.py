"""Unit tests for ParlayExplanationManager: fail-safe OpenAI explanation with fallback."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.parlay_explanation_manager import (
    ParlayExplanationManager,
    _fallback_explanation,
    _is_valid_explanation,
)


def test_is_valid_explanation():
    """Valid shape has summary and risk_notes."""
    assert _is_valid_explanation({"summary": "x", "risk_notes": "y"}) is True
    assert _is_valid_explanation({"summary": "x"}) is False
    assert _is_valid_explanation({"risk_notes": "y"}) is False
    assert _is_valid_explanation(None) is False
    assert _is_valid_explanation("string") is False


def test_fallback_explanation():
    """Fallback uses parlay_data and risk_profile."""
    parlay_data = {
        "legs": [{"game": "Team A vs Team B", "outcome": "A"}],
        "parlay_hit_prob": 0.25,
        "overall_confidence": 70.0,
    }
    out = _fallback_explanation(parlay_data, "balanced")
    assert "summary" in out and "risk_notes" in out
    assert "Balanced" in out["summary"]
    assert "25.0%" in out["summary"]
    assert "Team A vs Team B" in out["risk_notes"] or "volatility" in out["risk_notes"]


@pytest.mark.asyncio
async def test_get_explanation_openai_error_returns_fallback_and_flag():
    """When OpenAI raises, manager returns fallback explanation and explanation_fallback_used=True."""
    mock_openai = MagicMock(spec_set=["generate_parlay_explanation"])
    mock_openai.generate_parlay_explanation = AsyncMock(
        side_effect=RuntimeError("API key invalid")
    )
    manager = ParlayExplanationManager(openai_service=mock_openai)

    parlay_data = {
        "legs": [{"game": "A vs B", "market_type": "h2h", "outcome": "A", "odds": "-110", "confidence": 60.0}],
        "parlay_hit_prob": 0.2,
        "overall_confidence": 65.0,
    }

    with patch("app.services.parlay_explanation_manager.get_alerting_service") as mock_get_alert:
        mock_alert = MagicMock()
        mock_alert.emit = AsyncMock(return_value=True)
        mock_get_alert.return_value = mock_alert

        explanation, fallback_used, error_type = await manager.get_explanation(
            parlay_data=parlay_data,
            risk_profile="degen",
        )

    assert fallback_used is True
    assert error_type == "RuntimeError"
    assert "summary" in explanation and "risk_notes" in explanation
    assert "20.0%" in explanation["summary"]
    mock_alert.emit.assert_called_once()
    call_kw = mock_alert.emit.call_args
    assert call_kw[0][0] == "parlay.explanation_fallback"
    assert call_kw[0][1] == "warning"
    assert call_kw[0][2].get("error_type") == "RuntimeError"


@pytest.mark.asyncio
async def test_get_explanation_valid_openai_response_passed_through():
    """When OpenAI returns valid shape, manager returns it and explanation_fallback_used=False."""
    mock_openai = MagicMock(spec_set=["generate_parlay_explanation"])
    mock_openai.generate_parlay_explanation = AsyncMock(
        return_value={
            "summary": "Strong slate with balanced risk.",
            "risk_notes": "Watch the late game for line movement.",
        }
    )
    manager = ParlayExplanationManager(openai_service=mock_openai)

    parlay_data = {
        "legs": [{"game": "X vs Y", "market_type": "h2h", "outcome": "X", "odds": "-110", "confidence": 55.0}],
        "parlay_hit_prob": 0.15,
        "overall_confidence": 58.0,
    }

    explanation, fallback_used, error_type = await manager.get_explanation(
        parlay_data=parlay_data,
        risk_profile="balanced",
    )

    assert fallback_used is False
    assert error_type is None
    assert explanation["summary"] == "Strong slate with balanced risk."
    assert explanation["risk_notes"] == "Watch the late game for line movement."


@pytest.mark.asyncio
async def test_get_explanation_invalid_shape_uses_fallback():
    """When OpenAI returns dict missing summary/risk_notes, manager uses fallback."""
    mock_openai = MagicMock(spec_set=["generate_parlay_explanation"])
    mock_openai.generate_parlay_explanation = AsyncMock(
        return_value={"only_summary": "no risk_notes"}
    )
    manager = ParlayExplanationManager(openai_service=mock_openai)

    parlay_data = {
        "legs": [],
        "parlay_hit_prob": 0.1,
        "overall_confidence": 50.0,
    }

    with patch("app.services.parlay_explanation_manager.get_alerting_service") as mock_get_alert:
        mock_alert = MagicMock()
        mock_alert.emit = AsyncMock(return_value=True)
        mock_get_alert.return_value = mock_alert

        explanation, fallback_used, error_type = await manager.get_explanation(
            parlay_data=parlay_data,
            risk_profile="conservative",
        )

    assert fallback_used is True
    assert error_type == "ValueError"
    assert "summary" in explanation and "risk_notes" in explanation
    assert "Conservative" in explanation["summary"]
