"""
AI text sanitization utilities.

We store AI copy as plain text. If the model returns Markdown formatting (e.g., **bold**),
it will render as literal asterisks in the UI. This module normalizes AI output into
professional plain text.
"""

from __future__ import annotations

import re


class AiTextSanitizer:
    """
    Convert AI-generated Markdown-ish text into plain, analyst-style text.
    """

    _re_heading = re.compile(r"(?m)^#{1,6}[ \t]+")
    _re_bold = re.compile(r"\*\*(.+?)\*\*")
    _re_bold_underscore = re.compile(r"__(.+?)__")
    _re_inline_code = re.compile(r"`([^`]+)`")
    # Important: do NOT use \s here (it matches newlines and can collapse blank lines).
    _re_bullet = re.compile(r"(?m)^[ \t]*[-•][ \t]+")
    _re_numbered = re.compile(r"(?m)^[ \t]*\d+\.[ \t]+")
    _re_excess_newlines = re.compile(r"\n{3,}")

    def sanitize(self, text: str) -> str:
        if not text:
            return ""

        had_list_formatting = bool(self._re_bullet.search(text) or self._re_numbered.search(text))
        cleaned = text

        # Remove common markdown wrappers while keeping the content.
        cleaned = self._re_heading.sub("", cleaned)
        cleaned = self._re_bold.sub(r"\1", cleaned)
        cleaned = self._re_bold_underscore.sub(r"\1", cleaned)
        cleaned = self._re_inline_code.sub(r"\1", cleaned)

        # Remove list prefixes so we get paragraphs instead of a "markdown list" look.
        cleaned = self._re_bullet.sub("", cleaned)
        cleaned = self._re_numbered.sub("", cleaned)

        # If the model used list formatting, convert remaining single line breaks into
        # paragraph breaks so the result reads like prose.
        if had_list_formatting:
            cleaned = re.sub(r"(?m)(?<!\n)\n(?!\n)", "\n\n", cleaned)

        # As a final guard, remove stray emphasis asterisks.
        cleaned = cleaned.replace("*", "")

        # Normalize whitespace.
        cleaned = self._re_excess_newlines.sub("\n\n", cleaned).strip()

        return cleaned


