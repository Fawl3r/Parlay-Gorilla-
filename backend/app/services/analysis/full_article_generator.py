"""Long-form article generator (background).

This generator is intentionally separate from the core generator. Core must
render quickly; the full article can take longer and should run asynchronously.
"""

from __future__ import annotations

import asyncio
from typing import Any, Collection, Dict, Optional

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
        allowed_player_names: Optional[Collection[str]] = None,
        timeout_seconds: float = 90.0,
    ) -> str:
        if not self.enabled:
            return ""

        prompt = self._build_prompt(
            game=game,
            core_content=core_content,
            allowed_player_names=allowed_player_names,
        )
        system_content = (
            "You are a professional sports betting analyst and editor. "
            "Write clear, scannable prose with headings. "
            "Do not use markdown bullets; use short paragraphs. "
            "Do not guarantee outcomes. Emphasize responsible gambling. "
        )
        if allowed_player_names:
            names_list = ", ".join(sorted(set(allowed_player_names))[:150])
            system_content += (
                f"You may mention ONLY these player names (current rosters for this matchup): {names_list}. "
                "Do not mention any other specific player names."
            )
        else:
            system_content += (
                "Do not mention specific player names; use generic role-based phrasing (e.g. quarterback, running back, star playmaker)."
            )
        try:
            response = await asyncio.wait_for(
                self._openai.client.chat.completions.create(
                    model=self._openai.model,
                    messages=[
                        {"role": "system", "content": system_content},
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
    def _build_prompt(
        *,
        game: Game,
        core_content: Dict[str, Any],
        allowed_player_names: Optional[Collection[str]] = None,
    ) -> str:
        matchup = f"{game.away_team} @ {game.home_team}"
        spread_pick = (core_content.get("ai_spread_pick") or {}).get("pick", "")
        total_pick = (core_content.get("ai_total_pick") or {}).get("pick", "")
        probs = core_content.get("model_win_probability") or {}
        home_prob = probs.get("home_win_prob")
        away_prob = probs.get("away_win_prob")
        score_proj = probs.get("score_projection")

        prompt = (
            f"Write a 900-1400 word game preview for: {matchup} ({game.sport}).\n\n"
            "FORMATTING RULES:\n"
            "- Use markdown-style headings for structure (headings only; no markdown bullets).\n"
            "- Use EXACTLY these H2 headings, each on its own line:\n"
            "## Opening Summary\n"
            "## Matchup Breakdown\n"
            "## ATS Trends\n"
            "## Totals Trends\n"
            "## Model Projection\n"
            "## Best Bets\n"
            "## Responsible Gambling Note\n"
            "- Under 'Matchup Breakdown' and 'Best Bets', you MAY use H3 subheadings (###) for clarity.\n"
            "- Do NOT use bullet lists or numbered lists anywhere.\n"
            "- Write short paragraphs. Keep claims grounded in the provided data.\n\n"
            "Use the following precomputed info and do not invent injuries or stats:\n"
            f"- Model win prob: home={home_prob}, away={away_prob}\n"
            f"- Score projection: {score_proj}\n"
            f"- Spread pick: {spread_pick}\n"
            f"- Total pick: {total_pick}\n"
            f"- ATS: {core_content.get('ats_trends')}\n"
            f"- Totals: {core_content.get('totals_trends')}\n"
            f"- Best bets: {core_content.get('best_bets')}\n\n"
        )
        if allowed_player_names:
            prompt += (
                "RULES: Mention only the player names from the system message (current rosters for the two teams). Do not invent or mention any other player names. "
            )
        else:
            prompt += (
                "RULES: Do not mention specific player names; use generic role-based phrasing only. "
            )
        prompt += "Write in a confident, journalistic tone, but keep claims grounded in the provided data."
        return prompt


