"""
Parlay explanation manager: fail-safe OpenAI explanation with timeout and fallback.
Ensures parlay suggestions always return picks even when the LLM step fails.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

from app.services.openai_service import OpenAIService
from app.services.alerting import get_alerting_service

logger = logging.getLogger(__name__)

EXPLANATION_TIMEOUT_SECONDS = 12.0


def _fallback_explanation(parlay_data: Dict[str, Any], risk_profile: str) -> Dict[str, str]:
    """Build a deterministic fallback explanation when OpenAI fails."""
    legs = parlay_data.get("legs") or []
    prob = parlay_data.get("parlay_hit_prob", 0)
    summary = (
        f"{risk_profile.title()} parlay built from current slate. "
        f"Estimated hit rate: {prob:.1%}."
    )
    risk_notes = (
        "If odds move sharply or games get scratched/postponed, re-check before locking. "
        "Consider fewer legs for higher hit rate."
    )
    if legs:
        first = legs[0]
        matchup = first.get("matchup") or first.get("game") or "Top game"
        risk_notes = (
            f"{matchup}: volatility can swing outcomes — monitor late line movement. "
            + risk_notes
        )
    return {"summary": summary, "risk_notes": risk_notes}


def _is_valid_explanation(explanation: Any) -> bool:
    """Check that OpenAI returned the required shape."""
    return (
        isinstance(explanation, dict)
        and "summary" in explanation
        and "risk_notes" in explanation
    )


class ParlayExplanationManager:
    """
    Fail-safe parlay explanation: wraps OpenAI with timeout and fallback.
    On any error (timeout, rate limit, key, network), returns a deterministic
    explanation so the parlay endpoint never 500s due to the LLM step.
    """

    def __init__(
        self,
        openai_service: Optional[OpenAIService] = None,
        timeout_seconds: float = EXPLANATION_TIMEOUT_SECONDS,
    ):
        self._openai = openai_service or OpenAIService()
        self._timeout = timeout_seconds

    async def get_explanation(
        self,
        parlay_data: Dict[str, Any],
        risk_profile: str,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        sports: Optional[List[str]] = None,
    ) -> Tuple[Dict[str, str], bool, Optional[str]]:
        """
        Get parlay explanation with timeout and fallback.
        Returns (explanation_dict, explanation_fallback_used, error_type).
        """
        legs = parlay_data.get("legs") or []
        parlay_prob = parlay_data.get("parlay_hit_prob", 0.0)
        overall_conf = parlay_data.get("overall_confidence", 0.0)

        try:
            raw = await asyncio.wait_for(
                self._openai.generate_parlay_explanation(
                    legs=legs,
                    risk_profile=risk_profile,
                    parlay_probability=parlay_prob,
                    overall_confidence=overall_conf,
                ),
                timeout=self._timeout,
            )
            if not _is_valid_explanation(raw):
                raise ValueError("OpenAI explanation missing required keys (summary, risk_notes)")

            return (
                {"summary": str(raw["summary"]), "risk_notes": str(raw["risk_notes"])},
                False,
                None,
            )
        except Exception as e:
            error_type = type(e).__name__
            logger.warning(
                "OpenAI explanation failed; using fallback: %s: %s",
                error_type,
                e,
                extra={
                    "request_id": request_id,
                    "user_id": user_id,
                    "error_type": error_type,
                },
            )
            explanation = _fallback_explanation(parlay_data, risk_profile)
            await self._emit_fallback_alert(
                error_type=error_type,
                error_message=str(e),
                request_id=request_id,
                user_id=user_id,
                sports=sports,
            )
            return (explanation, True, error_type)

    async def _emit_fallback_alert(
        self,
        error_type: str,
        error_message: str,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        sports: Optional[List[str]] = None,
    ) -> None:
        """Emit a warning alert when explanation fallback is used."""
        try:
            payload: Dict[str, Any] = {
                "error_type": error_type,
                "error_message": (error_message or "")[:500],
            }
            if request_id:
                payload["request_id"] = request_id
            if user_id:
                payload["user_id"] = user_id
            if sports:
                payload["sports"] = sports
            await get_alerting_service().emit(
                "parlay.explanation_fallback",
                "warning",
                payload,
            )
        except Exception as alert_err:
            logger.debug("Alerting emit skipped: %s", alert_err)
