"""Optional OpenAI-backed writer for analysis copy.

Core analysis must be able to render without OpenAI. This writer is used to
polish copy when OpenAI is enabled and responsive, under strict timeouts.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, Optional

from app.services.openai_service import OpenAIService
from app.services.analysis.prompt_templates import AnalysisPromptTemplates


class AnalysisAiWriter:
    def __init__(self, openai: Optional[OpenAIService] = None):
        self._openai = openai or OpenAIService()

    @property
    def enabled(self) -> bool:
        return bool(getattr(self._openai, "_enabled", False))

    async def polish_core_copy(
        self,
        *,
        matchup: str,
        league: str,
        model_probs: Dict[str, Any],
        odds_snapshot: Dict[str, Any],
        draft: Dict[str, Any],
        timeout_seconds: float = 4.0,
    ) -> Dict[str, Any]:
        """
        Best-effort: rewrite ONLY the decision-first UI copy blocks (`ui_*`).

        Returns the updated draft (or the original on failure). Core analysis must
        remain valid even when OpenAI is disabled/unavailable.
        """
        if not self.enabled:
            return draft

        try:
            prompt = self._build_ui_prompt(
                matchup=matchup,
                league=league,
                model_probs=model_probs,
                odds_snapshot=odds_snapshot,
                draft=draft,
            )
            response = await asyncio.wait_for(
                self._openai.client.chat.completions.create(
                    model=self._openai.model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                f"{AnalysisPromptTemplates.MASTER_ANALYSIS_PROMPT}\n\n"
                                "Return valid JSON only."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.6,
                    max_tokens=550,
                    response_format={"type": "json_object"},
                ),
                timeout=timeout_seconds,
            )
            content = response.choices[0].message.content
            parsed = json.loads(content or "{}")
            return self._apply_ui_polish(draft=draft, polished=parsed)
        except Exception:
            return draft

    @staticmethod
    def _build_ui_prompt(
        *,
        matchup: str,
        league: str,
        model_probs: Dict[str, Any],
        odds_snapshot: Dict[str, Any],
        draft: Dict[str, Any],
    ) -> str:
        draft_ui = AnalysisAiWriter._extract_ui_subset(draft)

        return (
            "Polish the following UI copy blocks for a game analysis detail page.\n\n"
            "Goals:\n"
            "- Clear, confident, non-technical\n"
            "- No jargon\n"
            "- No stats (other than the provided confidence percent and bet line)\n"
            "- One recommendation per section\n\n"
            "You MUST keep the same JSON shape and keys.\n"
            "Only rewrite text fields (do not add new fields).\n\n"
            f"LEAGUE: {league}\n"
            f"MATCHUP: {matchup}\n"
            f"CONTEXT_MODEL: {json.dumps(model_probs)}\n"
            f"CONTEXT_ODDS: {json.dumps(odds_snapshot)}\n\n"
            f"DRAFT_UI: {json.dumps(draft_ui)}"
        )

    @staticmethod
    def _extract_ui_subset(draft: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "ui_quick_take": draft.get("ui_quick_take") or {},
            "ui_key_drivers": draft.get("ui_key_drivers") or {},
            "ui_bet_options": draft.get("ui_bet_options") or [],
            "ui_matchup_cards": draft.get("ui_matchup_cards") or [],
            "ui_trends": draft.get("ui_trends") or [],
        }

    @staticmethod
    def _apply_ui_polish(*, draft: Dict[str, Any], polished: Dict[str, Any]) -> Dict[str, Any]:
        updated = dict(draft)

        for key in ["ui_quick_take", "ui_key_drivers"]:
            block = polished.get(key)
            if isinstance(block, dict) and block:
                # Keep the entire object (same keys enforced by prompt).
                updated[key] = block

        for key in ["ui_bet_options", "ui_matchup_cards", "ui_trends"]:
            block = polished.get(key)
            if isinstance(block, list):
                updated[key] = block

        return updated


