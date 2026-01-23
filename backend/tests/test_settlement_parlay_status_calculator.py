"""Unit tests for ParlayStatusCalculator settlement logic."""

from __future__ import annotations

import pytest

from app.models.parlay_leg import ParlayLeg
from app.services.settlement.parlay_status_calculator import ParlayStatusCalculator


def _create_leg_with_status(status: str) -> ParlayLeg:
    """Helper to create a ParlayLeg with a specific status."""
    leg = ParlayLeg(
        market_type="h2h",
        selection="Team",
        status=status,
    )
    return leg


class TestAllLegsWon:
    """Tests when all legs are WON."""

    def test_single_leg_won(self):
        """Single leg WON → parlay WON."""
        legs = [_create_leg_with_status("WON")]
        result = ParlayStatusCalculator.calculate_status(legs)
        assert result == "WON"

    def test_multiple_legs_all_won(self):
        """All legs WON → parlay WON."""
        legs = [
            _create_leg_with_status("WON"),
            _create_leg_with_status("WON"),
            _create_leg_with_status("WON"),
        ]
        result = ParlayStatusCalculator.calculate_status(legs)
        assert result == "WON"


class TestAnyLegLost:
    """Tests when any leg is LOST."""

    def test_single_leg_lost(self):
        """Single leg LOST → parlay LOST."""
        legs = [_create_leg_with_status("LOST")]
        result = ParlayStatusCalculator.calculate_status(legs)
        assert result == "LOST"

    def test_first_leg_lost(self):
        """First leg LOST → parlay LOST (even if others WON)."""
        legs = [
            _create_leg_with_status("LOST"),
            _create_leg_with_status("WON"),
            _create_leg_with_status("WON"),
        ]
        result = ParlayStatusCalculator.calculate_status(legs)
        assert result == "LOST"

    def test_middle_leg_lost(self):
        """Middle leg LOST → parlay LOST."""
        legs = [
            _create_leg_with_status("WON"),
            _create_leg_with_status("LOST"),
            _create_leg_with_status("WON"),
        ]
        result = ParlayStatusCalculator.calculate_status(legs)
        assert result == "LOST"

    def test_last_leg_lost(self):
        """Last leg LOST → parlay LOST."""
        legs = [
            _create_leg_with_status("WON"),
            _create_leg_with_status("WON"),
            _create_leg_with_status("LOST"),
        ]
        result = ParlayStatusCalculator.calculate_status(legs)
        assert result == "LOST"

    def test_multiple_legs_lost(self):
        """Multiple legs LOST → parlay LOST."""
        legs = [
            _create_leg_with_status("LOST"),
            _create_leg_with_status("WON"),
            _create_leg_with_status("LOST"),
        ]
        result = ParlayStatusCalculator.calculate_status(legs)
        assert result == "LOST"


class TestAllLegsPush:
    """Tests when all legs are PUSH."""

    def test_single_leg_push(self):
        """Single leg PUSH → parlay PUSH."""
        legs = [_create_leg_with_status("PUSH")]
        result = ParlayStatusCalculator.calculate_status(legs)
        assert result == "PUSH"

    def test_multiple_legs_all_push(self):
        """All legs PUSH → parlay PUSH."""
        legs = [
            _create_leg_with_status("PUSH"),
            _create_leg_with_status("PUSH"),
            _create_leg_with_status("PUSH"),
        ]
        result = ParlayStatusCalculator.calculate_status(legs)
        assert result == "PUSH"


class TestMixedWonAndPush:
    """Tests when legs are mixed WON and PUSH."""

    def test_won_and_push(self):
        """Mixed WON and PUSH → parlay WON."""
        legs = [
            _create_leg_with_status("WON"),
            _create_leg_with_status("PUSH"),
            _create_leg_with_status("WON"),
        ]
        result = ParlayStatusCalculator.calculate_status(legs)
        assert result == "WON"

    def test_all_won_except_one_push(self):
        """All WON except one PUSH → parlay WON."""
        legs = [
            _create_leg_with_status("WON"),
            _create_leg_with_status("WON"),
            _create_leg_with_status("PUSH"),
        ]
        result = ParlayStatusCalculator.calculate_status(legs)
        assert result == "WON"


class TestLiveLegs:
    """Tests when any leg is LIVE."""

    def test_single_leg_live(self):
        """Single leg LIVE → parlay LIVE."""
        legs = [_create_leg_with_status("LIVE")]
        result = ParlayStatusCalculator.calculate_status(legs)
        assert result == "LIVE"

    def test_live_with_won_legs(self):
        """LIVE leg with WON legs → parlay LIVE."""
        legs = [
            _create_leg_with_status("WON"),
            _create_leg_with_status("LIVE"),
            _create_leg_with_status("WON"),
        ]
        result = ParlayStatusCalculator.calculate_status(legs)
        assert result == "LIVE"

    def test_live_with_pending_legs(self):
        """LIVE leg with PENDING legs → parlay LIVE."""
        legs = [
            _create_leg_with_status("PENDING"),
            _create_leg_with_status("LIVE"),
            _create_leg_with_status("PENDING"),
        ]
        result = ParlayStatusCalculator.calculate_status(legs)
        assert result == "LIVE"

    def test_live_but_leg_lost(self):
        """LIVE leg but another leg LOST → parlay LOST (LOST takes precedence)."""
        legs = [
            _create_leg_with_status("WON"),
            _create_leg_with_status("LOST"),
            _create_leg_with_status("LIVE"),
        ]
        result = ParlayStatusCalculator.calculate_status(legs)
        assert result == "LOST"


class TestPendingLegs:
    """Tests when legs are PENDING."""

    def test_single_leg_pending(self):
        """Single leg PENDING → parlay PENDING."""
        legs = [_create_leg_with_status("PENDING")]
        result = ParlayStatusCalculator.calculate_status(legs)
        assert result == "PENDING"

    def test_all_legs_pending(self):
        """All legs PENDING → parlay PENDING."""
        legs = [
            _create_leg_with_status("PENDING"),
            _create_leg_with_status("PENDING"),
            _create_leg_with_status("PENDING"),
        ]
        result = ParlayStatusCalculator.calculate_status(legs)
        assert result == "PENDING"

    def test_pending_with_won_legs(self):
        """PENDING leg with WON legs → parlay PENDING."""
        legs = [
            _create_leg_with_status("WON"),
            _create_leg_with_status("PENDING"),
            _create_leg_with_status("WON"),
        ]
        result = ParlayStatusCalculator.calculate_status(legs)
        assert result == "PENDING"


class TestVoidLegs:
    """Tests when legs are VOID."""

    def test_single_leg_void(self):
        """Single leg VOID → parlay VOID."""
        legs = [_create_leg_with_status("VOID")]
        result = ParlayStatusCalculator.calculate_status(legs)
        assert result == "VOID"

    def test_all_legs_void(self):
        """All legs VOID → parlay VOID."""
        legs = [
            _create_leg_with_status("VOID"),
            _create_leg_with_status("VOID"),
            _create_leg_with_status("VOID"),
        ]
        result = ParlayStatusCalculator.calculate_status(legs)
        assert result == "VOID"

    def test_mixed_void_and_won(self):
        """Mixed VOID and WON → parlay PENDING (VOID treated as neutral, but has PENDING fallback)."""
        legs = [
            _create_leg_with_status("VOID"),
            _create_leg_with_status("WON"),
            _create_leg_with_status("VOID"),
        ]
        # Current implementation: Mixed VOID doesn't explicitly return WON, falls through to PENDING
        # This is a business rule that may need clarification
        result = ParlayStatusCalculator.calculate_status(legs)
        # Based on current logic: VOID is checked, but if not all VOID, it continues
        # Since no LOST, no LIVE, no PENDING in statuses, and not all WON/PUSH, falls to PENDING
        # Actually, WON is in the list, so it should check if all are WON or PUSH
        # But VOID is not in ("WON", "PUSH"), so all() check fails
        # Falls through to PENDING
        assert result == "PENDING"


class TestEmptyLegs:
    """Tests edge cases with empty or invalid leg lists."""

    def test_empty_legs_list(self):
        """Empty legs list → parlay PENDING."""
        legs = []
        result = ParlayStatusCalculator.calculate_status(legs)
        assert result == "PENDING"


class TestComplexScenarios:
    """Tests for complex real-world scenarios."""

    def test_parlay_with_all_statuses_except_lost(self):
        """Parlay with WON, PUSH, LIVE, PENDING → parlay LIVE (LIVE takes precedence over PENDING)."""
        legs = [
            _create_leg_with_status("WON"),
            _create_leg_with_status("PUSH"),
            _create_leg_with_status("LIVE"),
            _create_leg_with_status("PENDING"),
        ]
        result = ParlayStatusCalculator.calculate_status(legs)
        assert result == "LIVE"

    def test_parlay_progression_pending_to_live_to_won(self):
        """Simulate parlay progression: all PENDING → all LIVE → all WON."""
        # Stage 1: All PENDING
        legs_pending = [
            _create_leg_with_status("PENDING"),
            _create_leg_with_status("PENDING"),
        ]
        assert ParlayStatusCalculator.calculate_status(legs_pending) == "PENDING"

        # Stage 2: Some LIVE
        legs_live = [
            _create_leg_with_status("LIVE"),
            _create_leg_with_status("PENDING"),
        ]
        assert ParlayStatusCalculator.calculate_status(legs_live) == "LIVE"

        # Stage 3: All WON
        legs_won = [
            _create_leg_with_status("WON"),
            _create_leg_with_status("WON"),
        ]
        assert ParlayStatusCalculator.calculate_status(legs_won) == "WON"

    def test_parlay_busts_early(self):
        """Parlay with first leg LOST → immediately LOST (others don't matter)."""
        legs = [
            _create_leg_with_status("LOST"),
            _create_leg_with_status("PENDING"),
            _create_leg_with_status("PENDING"),
        ]
        result = ParlayStatusCalculator.calculate_status(legs)
        assert result == "LOST"

    def test_large_parlay_all_won(self):
        """Large parlay (10 legs) all WON → parlay WON."""
        legs = [_create_leg_with_status("WON") for _ in range(10)]
        result = ParlayStatusCalculator.calculate_status(legs)
        assert result == "WON"

    def test_large_parlay_one_lost(self):
        """Large parlay (10 legs) with one LOST → parlay LOST."""
        legs = [_create_leg_with_status("WON") for _ in range(9)]
        legs.append(_create_leg_with_status("LOST"))
        result = ParlayStatusCalculator.calculate_status(legs)
        assert result == "LOST"
