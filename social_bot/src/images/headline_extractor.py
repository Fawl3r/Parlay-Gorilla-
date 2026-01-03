from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Tuple


_URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
_DIGIT_TOKEN_RE = re.compile(r"\b\S*\d\S*\b")
_NON_LETTER_RE = re.compile(r"[^A-Za-z\s']+")
_MULTI_SPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class HeadlineText:
    headline: str
    subtext: Optional[str] = None


class HeadlineExtractor:
    def extract(self, *, post_text: str, pillar_id: str, template_id: str) -> HeadlineText:
        template = (template_id or "").strip().lower()
        cleaned = self._strip_urls_and_noise(post_text or "")
        from_template = self._template_headline(template)
        if from_template is not None:
            headline, subtext = from_template
            return self._finalize(headline=headline, subtext=subtext)

        fallback = self._fallback_from_text(cleaned)
        if fallback:
            return self._finalize(headline=fallback, subtext=None)

        # Last resort: brand-safe, content-agnostic line.
        return self._finalize(headline="BET SMARTER AND STAY DISCIPLINED OVER THE LONG RUN", subtext=None)

    def _template_headline(self, template: str) -> Optional[Tuple[str, Optional[str]]]:
        mapping: dict[str, Tuple[str, Optional[str]]] = {
            "analysis_matchup_angle": ("MATCHUP CONTEXT BEATS VIBES IN THE LONG RUN", None),
            "analysis_risk_note": ("RESPECT THE RISK BEFORE YOU CHASE THE HYPE", None),
            "matchup_watch": ("WATCH THE MATCHUP CONTEXT NOT THE NARRATIVE", None),
            "matchup_question": ("ASK WHAT REALLY DRIVES THIS MATCHUP EDGE", None),
            "quick_checklist": ("BEFORE YOU BET CHECK THESE THINGS FIRST ALWAYS", None),
            "micro_tip": ("ONE SMALL EDGE TODAY ADDS UP OVER TIME", None),
            "engage_question": ("DO YOU BET THE NUMBER OR THE NARRATIVE", None),
            "discipline_unit_size": ("KEEP YOUR UNIT SIZE BORING PROTECT YOUR BANKROLL", None),
            "discipline_line_shopping": ("LINE SHOPPING IS THE EASIEST EDGE YOU CAN TAKE", None),
            "market_price_matter": ("A GREAT PICK AT A BAD PRICE STILL LOSES", None),
            "market_public_vs_sharp": ("ASK WHY THE LINE MOVED BEFORE YOU TAIL", None),
            "feature_spotlight": ("BUILD SMARTER PARLAYS WITH A CLEAN DASHBOARD", None),
            "cta_analysis_hub": ("GET CLEAN MATCHUP BREAKDOWNS BEFORE YOU BET", None),
            "cta_build": ("BUILD FAST BUT STAY DISCIPLINED IN THE LONG RUN", None),
            "cta_tutorial": ("START WITH THE BASICS THEN BUILD SMARTER", None),
            "cta_pricing": ("KNOW WHAT YOU GET BEFORE YOU COMMIT", None),
            "cta_value_prop": ("BET WITH CONTEXT NOT WITH VIBES", None),
        }
        return mapping.get(template)

    def _fallback_from_text(self, cleaned: str) -> str:
        # Prefer the first meaningful line that isn't a label.
        for raw_line in (cleaned or "").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.lower().startswith(("key points:", "risk note:", "read:", "angle:")):
                continue
            normalized = self._sanitize(line)
            if normalized:
                return normalized
        return ""

    def _strip_urls_and_noise(self, text: str) -> str:
        without_urls = _URL_RE.sub("", text or "")
        lines = []
        for raw in without_urls.splitlines():
            s = raw.strip()
            if not s:
                continue
            if "http" in s.lower():
                continue
            lines.append(s)
        return "\n".join(lines)

    def _sanitize(self, value: str) -> str:
        s = (value or "").strip()
        if not s:
            return ""
        s = _DIGIT_TOKEN_RE.sub("", s)
        s = _NON_LETTER_RE.sub(" ", s)
        s = _MULTI_SPACE_RE.sub(" ", s).strip()
        return s

    def _finalize(self, *, headline: str, subtext: Optional[str]) -> HeadlineText:
        head = self._enforce_word_range(self._sanitize(headline), min_words=8, max_words=12)
        sub = self._sanitize(subtext or "") if subtext else ""

        if sub:
            sub = self._enforce_word_range(sub, min_words=0, max_words=10)
            if self._count_words(head) + self._count_words(sub) > 20:
                sub = ""

        return HeadlineText(headline=head.upper(), subtext=(sub.upper() if sub else None))

    def _enforce_word_range(self, value: str, *, min_words: int, max_words: int) -> str:
        words = [w for w in (value or "").split() if w]
        if not words:
            return ""
        if len(words) > max_words:
            return " ".join(words[:max_words])
        if len(words) < min_words:
            filler = ["IN", "THE", "LONG", "RUN"]
            while len(words) < min_words and filler:
                words.append(filler.pop(0))
        return " ".join(words)

    def _count_words(self, value: str) -> int:
        return len([w for w in (value or "").split() if w])


