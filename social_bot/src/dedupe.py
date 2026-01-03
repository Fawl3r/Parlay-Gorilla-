from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import List, Optional

from src.models import QueueItem, parse_iso8601, text_sha256


@dataclass(frozen=True)
class DedupeDecision:
    ok: bool
    reason: Optional[str] = None


class DedupeEngine:
    def __init__(
        self,
        *,
        similarity_threshold: float,
        template_cooldown_hours: int,
        pillar_cooldown_hours: int,
        recent_window_items: int,
        exempt_template_ids: Optional[List[str]] = None,
    ) -> None:
        self._similarity_threshold = float(similarity_threshold)
        self._template_cooldown = timedelta(hours=int(template_cooldown_hours))
        self._pillar_cooldown = timedelta(hours=int(pillar_cooldown_hours))
        self._recent_window_items = int(recent_window_items)
        self._exempt_template_ids = set(exempt_template_ids or [])

    def check(
        self,
        *,
        candidate: QueueItem,
        outbox: List[QueueItem],
        posted_raw: List[dict],
        now: datetime,
    ) -> DedupeDecision:
        if candidate.template_id in self._exempt_template_ids:
            return DedupeDecision(ok=True)

        decision = self._check_similarity(candidate, outbox, posted_raw)
        if not decision.ok:
            return decision

        decision = self._check_exact_hash(candidate, posted_raw)
        if not decision.ok:
            return decision

        decision = self._check_template_cooldown(candidate, posted_raw, now)
        if not decision.ok:
            return decision

        decision = self._check_pillar_cooldown(candidate, posted_raw, now)
        if not decision.ok:
            return decision

        return DedupeDecision(ok=True)

    def is_hook_recently_used(self, hook_text: str, *, outbox: List[QueueItem], posted_raw: List[dict]) -> bool:
        needle = (hook_text or "").strip()
        if not needle:
            return False
        recent_texts = [x.flattened_text() for x in outbox][-self._recent_window_items :]
        for raw in posted_raw[-self._recent_window_items :]:
            if isinstance(raw.get("text"), str):
                recent_texts.append(raw["text"])
            elif isinstance(raw.get("tweets"), list):
                recent_texts.append("\n".join(str(x) for x in raw.get("tweets") or []))
        return any(needle in (t or "") for t in recent_texts)

    def _check_similarity(self, candidate: QueueItem, outbox: List[QueueItem], posted_raw: List[dict]) -> DedupeDecision:
        cand = self._normalize(candidate.flattened_text())
        for existing in outbox[-self._recent_window_items :]:
            other = self._normalize(existing.flattened_text())
            if not other:
                continue
            ratio = SequenceMatcher(a=cand, b=other).ratio()
            if ratio >= self._similarity_threshold:
                return DedupeDecision(ok=False, reason=f"Too similar to outbox item {existing.id} ({ratio:.2f})")
        for raw in posted_raw[-self._recent_window_items :]:
            other_text: str = ""
            if isinstance(raw.get("text"), str):
                other_text = raw["text"]
            elif isinstance(raw.get("tweets"), list):
                other_text = "\n".join(str(x) for x in raw.get("tweets") or [])
            other = self._normalize(other_text)
            if not other:
                continue
            ratio = SequenceMatcher(a=cand, b=other).ratio()
            if ratio >= self._similarity_threshold:
                return DedupeDecision(ok=False, reason=f"Too similar to previously posted content ({ratio:.2f})")
        return DedupeDecision(ok=True)

    def _check_exact_hash(self, candidate: QueueItem, posted_raw: List[dict]) -> DedupeDecision:
        cand_hash = text_sha256(candidate.flattened_text())
        for raw in posted_raw[-self._recent_window_items :]:
            if str(raw.get("text_hash") or "") == cand_hash:
                return DedupeDecision(ok=False, reason="Exact duplicate of previously posted content")
        return DedupeDecision(ok=True)

    def _check_template_cooldown(self, candidate: QueueItem, posted_raw: List[dict], now: datetime) -> DedupeDecision:
        if self._template_cooldown.total_seconds() <= 0:
            return DedupeDecision(ok=True)
        for raw in reversed(posted_raw):
            if str(raw.get("template_id") or "") != candidate.template_id:
                continue
            posted_at = parse_iso8601(str(raw.get("posted_at") or ""))
            if now - posted_at < self._template_cooldown:
                return DedupeDecision(ok=False, reason="Template cooldown active")
            return DedupeDecision(ok=True)
        return DedupeDecision(ok=True)

    def _check_pillar_cooldown(self, candidate: QueueItem, posted_raw: List[dict], now: datetime) -> DedupeDecision:
        if self._pillar_cooldown.total_seconds() <= 0:
            return DedupeDecision(ok=True)
        for raw in reversed(posted_raw):
            if str(raw.get("pillar_id") or "") != candidate.pillar_id:
                continue
            posted_at = parse_iso8601(str(raw.get("posted_at") or ""))
            if now - posted_at < self._pillar_cooldown:
                return DedupeDecision(ok=False, reason="Pillar cooldown active")
            return DedupeDecision(ok=True)
        return DedupeDecision(ok=True)

    def _normalize(self, text: str) -> str:
        return " ".join((text or "").lower().split())


