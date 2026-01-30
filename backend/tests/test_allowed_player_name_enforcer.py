"""
Tests for AllowedPlayerNameEnforcer: allowlisted names preserved, others redacted.
"""

import pytest

from app.services.analysis.allowed_player_name_enforcer import AllowedPlayerNameEnforcer


class TestAllowedPlayerNameEnforcer:
    """AllowedPlayerNameEnforcer.enforce(text, allowed_player_names) behavior."""

    def test_empty_allowlist_redacts_all(self) -> None:
        enforcer = AllowedPlayerNameEnforcer()
        text = "The Seahawks are led by Geno Smith. Quarterback Patrick Mahomes will start."
        out, _ = enforcer.enforce(text, allowed_player_names=[])
        assert "Geno Smith" not in out
        assert "Patrick Mahomes" not in out
        assert "led by its core playmakers" in out
        assert "Quarterback" in out

    def test_allowlisted_name_preserved(self) -> None:
        enforcer = AllowedPlayerNameEnforcer()
        text = "The Seahawks are led by Geno Smith. Star Patrick Mahomes will shine."
        out, _ = enforcer.enforce(text, allowed_player_names=["Geno Smith"])
        assert "Geno Smith" in out
        assert "led by Geno Smith" in out
        assert "Patrick Mahomes" not in out
        assert "Star" in out

    def test_both_allowlisted_both_preserved(self) -> None:
        enforcer = AllowedPlayerNameEnforcer()
        # Use "Name will" so NAME_WILL pattern keeps allowlisted name
        text = "Led by Geno Smith. Patrick Mahomes will lead the offense."
        out, _ = enforcer.enforce(
            text,
            allowed_player_names=["Geno Smith", "Patrick Mahomes"],
        )
        assert "Geno Smith" in out
        assert "Patrick Mahomes" in out
        assert "led by its core playmakers" not in out
        assert "The unit will" not in out

    def test_none_allowlist_redacts_all(self) -> None:
        enforcer = AllowedPlayerNameEnforcer()
        text = "Star Tyreek Hill will score."
        out, _ = enforcer.enforce(text, allowed_player_names=None)
        assert "Tyreek Hill" not in out
        assert "Star" in out

    def test_headings_preserved(self) -> None:
        enforcer = AllowedPlayerNameEnforcer()
        text = "## Matchup Breakdown\n\nLed by Joe Burrow."
        out, _ = enforcer.enforce(text, allowed_player_names=[])
        assert "## Matchup Breakdown" in out
        assert "Led by" in out or "led by" in out
        assert "Joe Burrow" not in out

    def test_redaction_count_increments_correctly(self) -> None:
        enforcer = AllowedPlayerNameEnforcer()
        # Two disallowed names; one allowlisted (Geno Smith) preserved
        text = "Led by Geno Smith. Star Patrick Mahomes will shine. Quarterback Joe Montana will start."
        out, redaction_count = enforcer.enforce(
            text, allowed_player_names=["Geno Smith"]
        )
        assert "Geno Smith" in out
        assert "led by Geno Smith" in out or "Led by Geno Smith" in out
        assert "Patrick Mahomes" not in out
        assert "Joe Montana" not in out
        assert "Star" in out
        assert redaction_count == 2
