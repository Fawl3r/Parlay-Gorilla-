"""
AI text normalization utilities.

We occasionally receive AI-generated JSON that contains *literal* escape sequences
inside string fields (e.g. "\\n\\n" instead of real newlines). This module
normalizes those sequences for downstream consumers (API responses, storage, UI).
"""

from __future__ import annotations

from typing import Any, Dict, List


class AiTextNormalizer:
    """Normalize escaped sequences in AI-generated content."""

    def normalize_escaped_newlines(self, text: str) -> str:
        if not text:
            return ""

        # Order matters: normalize CRLF first, then LF.
        return (
            text.replace("\\r\\n", "\n")
            .replace("\\n", "\n")
            .replace("\\t", "\t")
        )

    def normalize_obj(self, obj: Any) -> Any:
        """
        Recursively normalize strings inside dict/list structures.

        This is intentionally conservative: it only normalizes common newline/tab
        escape sequences used in long-form AI copy.
        """
        if obj is None:
            return None
        if isinstance(obj, str):
            return self.normalize_escaped_newlines(obj)
        if isinstance(obj, list):
            return [self.normalize_obj(v) for v in obj]
        if isinstance(obj, dict):
            return {k: self.normalize_obj(v) for k, v in obj.items()}
        return obj





