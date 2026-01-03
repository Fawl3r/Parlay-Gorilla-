from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional


class GuardianRejectError(RuntimeError):
    pass


_EMOJI_RE = re.compile(r"[\U0001F300-\U0001FAFF]")
_HASHTAG_RE = re.compile(r"(#[A-Za-z0-9_]+)")


@dataclass(frozen=True)
class GuardianResult:
    text: str
    rejected_reason: Optional[str] = None


class ComplianceGuardian:
    def __init__(
        self,
        *,
        banned_phrases: List[str],
        max_length: int,
        max_hashtags: int,
        max_emojis: int,
        banned_phrase_action: str,
    ) -> None:
        self._banned_phrases = [p.strip().lower() for p in banned_phrases if p.strip()]
        self._max_length = int(max_length)
        self._max_hashtags = int(max_hashtags)
        self._max_emojis = int(max_emojis)
        self._banned_phrase_action = (banned_phrase_action or "reject").strip().lower()

    def enforce_single(self, text: str) -> str:
        cleaned = self._normalize(text)
        cleaned = self._enforce_banned_phrases(cleaned)
        cleaned = self._enforce_hashtags(cleaned)
        cleaned = self._enforce_emojis(cleaned)
        cleaned = self._enforce_length(cleaned)
        return cleaned

    def enforce_thread(self, tweets: List[str]) -> List[str]:
        if not tweets:
            raise GuardianRejectError("Empty thread")
        enforced: List[str] = []
        for t in tweets:
            enforced.append(self.enforce_single(t))
        return enforced

    def _normalize(self, text: str) -> str:
        value = (text or "").replace("\r\n", "\n").strip()
        value = re.sub(r"[ \t]+", " ", value)
        value = re.sub(r"\n{3,}", "\n\n", value)
        return value

    def _enforce_banned_phrases(self, text: str) -> str:
        lowered = text.lower()
        hits = [p for p in self._banned_phrases if p and p in lowered]
        if not hits:
            return text
        if self._banned_phrase_action == "sanitize":
            sanitized = text
            for phrase in hits:
                sanitized = re.sub(re.escape(phrase), "", sanitized, flags=re.IGNORECASE)
            return self._normalize(sanitized)
        raise GuardianRejectError(f"Banned phrase(s): {', '.join(hits[:3])}")

    def _enforce_hashtags(self, text: str) -> str:
        if self._max_hashtags <= 0:
            return text
        tags = _HASHTAG_RE.findall(text)
        if len(tags) <= self._max_hashtags:
            return text
        if self._banned_phrase_action == "sanitize":
            kept = set(tags[: self._max_hashtags])
            parts = []
            for token in text.split(" "):
                if token.startswith("#") and token in tags and token not in kept:
                    continue
                parts.append(token)
            return self._normalize(" ".join(parts))
        raise GuardianRejectError(f"Too many hashtags ({len(tags)}>{self._max_hashtags})")

    def _enforce_emojis(self, text: str) -> str:
        if self._max_emojis <= 0:
            return text
        emojis = _EMOJI_RE.findall(text)
        if len(emojis) <= self._max_emojis:
            return text
        if self._banned_phrase_action == "sanitize":
            remaining = self._max_emojis
            out_chars: List[str] = []
            for ch in text:
                if _EMOJI_RE.match(ch):
                    if remaining <= 0:
                        continue
                    remaining -= 1
                out_chars.append(ch)
            return self._normalize("".join(out_chars))
        raise GuardianRejectError(f"Too many emojis ({len(emojis)}>{self._max_emojis})")

    def _enforce_length(self, text: str) -> str:
        if len(text) <= self._max_length:
            return text
        if self._banned_phrase_action == "sanitize":
            return text[: self._max_length].rstrip()
        raise GuardianRejectError(f"Too long ({len(text)}>{self._max_length})")


