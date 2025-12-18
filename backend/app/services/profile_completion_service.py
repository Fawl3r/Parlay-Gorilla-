"""
Profile completion consistency helpers.

Goal: ensure we don't repeatedly force users through `/profile/setup` when they
already completed it (or have equivalent profile data persisted).

This is intentionally lightweight and side-effect free (no DB commits).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.models.user import User


@dataclass(frozen=True)
class ProfileCompletionService:
    """
    Encapsulates logic for deciding when a profile should be considered completed.
    """

    def apply_auto_completion(self, user: User) -> bool:
        """
        Mutates the passed `user` in-memory if we can confidently mark them as complete.

        Returns:
            True if the user object was mutated (profile_completed flipped to True).
        """
        if getattr(user, "profile_completed", False):
            return False

        display_name = (getattr(user, "display_name", None) or "").strip()
        if display_name:
            user.profile_completed = True
            return True

        return False





