"""Email normalization utilities.

Centralizes the app's definition of "equivalent emails" so that:
- Users can log in regardless of casing/whitespace differences.
- We avoid accidental duplicate accounts (especially before DB constraints exist).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class EmailNormalizer:
    """Normalizes user emails for consistent storage + lookup."""

    def normalize(self, email: str) -> str:
        return (email or "").strip().lower()

    def normalize_optional(self, email: Optional[str]) -> Optional[str]:
        normalized = self.normalize(email or "")
        return normalized or None


