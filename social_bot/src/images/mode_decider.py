from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Dict, Optional, Tuple

from src.images.image_mode import ImageMode


@dataclass(frozen=True)
class ImageModeDecision:
    mode: ImageMode
    reason: str


class ImageModeDecider:
    def decide(
        self,
        *,
        pillar_id: str,
        template_id: str,
        rng: Optional[Random] = None,
    ) -> ImageModeDecision:
        pillar = (pillar_id or "").strip().lower()
        template = (template_id or "").strip().lower()
        rng = rng or Random()

        if template in {"analysis_matchup_angle", "analysis_risk_note"}:
            return ImageModeDecision(mode=ImageMode.analysis_card, reason="analysis_template")

        if template.startswith("cta_") or template == "feature_spotlight" or pillar == "product_cta":
            return ImageModeDecision(mode=self._weighted(rng, {ImageMode.ui_tease: 0.7, ImageMode.quote_card: 0.2, ImageMode.generic: 0.1}), reason="product_cta")

        if pillar in {"betting_discipline", "market_notes"}:
            return ImageModeDecision(mode=self._weighted(rng, {ImageMode.quote_card: 0.75, ImageMode.persona: 0.15, ImageMode.generic: 0.10}), reason="discipline_or_market")

        return ImageModeDecision(mode=self._weighted(rng, {ImageMode.generic: 0.7, ImageMode.quote_card: 0.3}), reason="default")

    def _weighted(self, rng: Random, weights: Dict[ImageMode, float]) -> ImageMode:
        items: Tuple[Tuple[ImageMode, float], ...] = tuple((m, float(w)) for m, w in weights.items() if float(w) > 0)
        total = sum(w for _, w in items)
        if not items or total <= 0:
            return ImageMode.generic
        pick = rng.random() * total
        upto = 0.0
        for mode, weight in items:
            upto += weight
            if pick <= upto:
                return mode
        return items[-1][0]


