"""Long-form article generator (background).

This generator is intentionally separate from the core generator. Core must
render quickly; the full article can take longer and should run asynchronously.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from app.models.game import Game
from app.services.openai_service import OpenAIService


class FullArticleGenerator:
    def __init__(self, openai: Optional[OpenAIService] = None):
        self._openai = openai or OpenAIService()

    @property
    def enabled(self) -> bool:
        return bool(getattr(self._openai, "_enabled", False))

    async def generate(
        self,
        *,
        game: Game,
        core_content: Dict[str, Any],
        timeout_seconds: float = 90.0,
    ) -> str:
        if not self.enabled:
            return ""

        prompt = self._build_prompt(game=game, core_content=core_content)
        try:
            response = await asyncio.wait_for(
                self._openai.client.chat.completions.create(
                    model=self._openai.model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a professional sports betting analyst and editor. "
                                "Write clear, scannable prose with headings. "
                                "Do not use markdown bullets; use short paragraphs. "
                                "Do not guarantee outcomes. Emphasize responsible gambling."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                    max_tokens=2200,
                ),
                timeout=timeout_seconds,
            )
            text = (response.choices[0].message.content or "").strip()
            return text
        except Exception:
            return ""

    @staticmethod
    def _build_prompt(*, game: Game, core_content: Dict[str, Any]) -> str:
        matchup = f"{game.away_team} @ {game.home_team}"
        spread_pick = (core_content.get("ai_spread_pick") or {}).get("pick", "")
        total_pick = (core_content.get("ai_total_pick") or {}).get("pick", "")
        probs = core_content.get("model_win_probability") or {}
        home_prob = probs.get("home_win_prob")
        away_prob = probs.get("away_win_prob")
        score_proj = probs.get("score_projection")

        return (
            f"Write a 900-1400 word game preview for: {matchup} ({game.sport}).\n\n"
            "Structure with short headings (plain text):\n"
            "1) Opening Summary\n"
            "2) Matchup Breakdown\n"
            "3) ATS Trends\n"
            "4) Totals Trends\n"
            "5) Model Projection\n"
            "6) Best Bets\n"
            "7) Responsible Gambling Note\n\n"
            "Use the following precomputed info and do not invent injuries or stats:\n"
            f"- Model win prob: home={home_prob}, away={away_prob}\n"
            f"- Score projection: {score_proj}\n"
            f"- Spread pick: {spread_pick}\n"
            f"- Total pick: {total_pick}\n"
            f"- ATS: {core_content.get('ats_trends')}\n"
            f"- Totals: {core_content.get('totals_trends')}\n"
            f"- Best bets: {core_content.get('best_bets')}\n\n"
            "Write in a confident, journalistic tone, but keep claims grounded in the provided data."
        )


