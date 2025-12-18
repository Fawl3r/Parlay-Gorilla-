"""Optional OpenAI-backed writer for analysis copy.

Core analysis must be able to render without OpenAI. This writer is used to
polish copy when OpenAI is enabled and responsive, under strict timeouts.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, Optional

from app.services.openai_service import OpenAIService


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
        Best-effort: rewrite opening_summary + pick rationales.

        Returns the updated draft (or the original on failure).
        """
        if not self.enabled:
            return draft

        try:
            prompt = self._build_prompt(
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
                                "You are a concise sports betting analyst. "
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
            return self._apply_polish(draft=draft, polished=parsed)
        except Exception:
            return draft

    @staticmethod
    def _build_prompt(
        *,
        matchup: str,
        league: str,
        model_probs: Dict[str, Any],
        odds_snapshot: Dict[str, Any],
        draft: Dict[str, Any],
    ) -> str:
        return (
            "Rewrite only these fields for clarity and professionalism:\n"
            "- opening_summary (3-4 sentences)\n"
            "- ai_spread_pick.rationale (1-2 sentences)\n"
            "- ai_total_pick.rationale (1-2 sentences)\n"
            "- best_bets[0..2].rationale (1-2 sentences each)\n\n"
            f"LEAGUE: {league}\n"
            f"MATCHUP: {matchup}\n"
            f"MODEL: {json.dumps(model_probs)}\n"
            f"ODDS: {json.dumps(odds_snapshot)}\n\n"
            "Return JSON with the same keys as the provided draft subset.\n"
            f"DRAFT_SUBSET: {json.dumps(AnalysisAiWriter._extract_subset(draft))}"
        )

    @staticmethod
    def _extract_subset(draft: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "opening_summary": draft.get("opening_summary", ""),
            "ai_spread_pick": {"rationale": (draft.get("ai_spread_pick") or {}).get("rationale", "")},
            "ai_total_pick": {"rationale": (draft.get("ai_total_pick") or {}).get("rationale", "")},
            "best_bets": [
                {"rationale": (b or {}).get("rationale", "")}
                for b in (draft.get("best_bets") or [])[:3]
            ],
        }

    @staticmethod
    def _apply_polish(*, draft: Dict[str, Any], polished: Dict[str, Any]) -> Dict[str, Any]:
        updated = dict(draft)

        opening = polished.get("opening_summary")
        if isinstance(opening, str) and opening.strip():
            updated["opening_summary"] = opening.strip()

        for key in ["ai_spread_pick", "ai_total_pick"]:
            block = polished.get(key)
            if isinstance(block, dict):
                rationale = block.get("rationale")
                if isinstance(rationale, str) and rationale.strip():
                    existing = dict(updated.get(key) or {})
                    existing["rationale"] = rationale.strip()
                    updated[key] = existing

        polished_bets = polished.get("best_bets")
        if isinstance(polished_bets, list):
            bets = list(updated.get("best_bets") or [])
            for i in range(min(3, len(bets), len(polished_bets))):
                rationale = (polished_bets[i] or {}).get("rationale")
                if isinstance(rationale, str) and rationale.strip() and isinstance(bets[i], dict):
                    bets[i] = {**bets[i], "rationale": rationale.strip()}
            updated["best_bets"] = bets

        return updated


