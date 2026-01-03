from __future__ import annotations

import pytest

from src.guardian import ComplianceGuardian, GuardianRejectError


def test_guardian_rejects_banned_phrase() -> None:
    g = ComplianceGuardian(
        banned_phrases=["free money"],
        max_length=280,
        max_hashtags=2,
        max_emojis=2,
        banned_phrase_action="reject",
    )
    with pytest.raises(GuardianRejectError):
        g.enforce_single("This is FREE money!!!")


def test_guardian_sanitizes_banned_phrase_when_configured() -> None:
    g = ComplianceGuardian(
        banned_phrases=["free money"],
        max_length=280,
        max_hashtags=2,
        max_emojis=2,
        banned_phrase_action="sanitize",
    )
    out = g.enforce_single("This is free money!!!")
    assert "free money" not in out.lower()


def test_guardian_hashtag_cap_sanitize() -> None:
    g = ComplianceGuardian(
        banned_phrases=[],
        max_length=280,
        max_hashtags=2,
        max_emojis=2,
        banned_phrase_action="sanitize",
    )
    out = g.enforce_single("Hi #a #b #c")
    assert out.count("#") <= 2


