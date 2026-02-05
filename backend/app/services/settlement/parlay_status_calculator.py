"""Parlay status calculator based on leg results."""

from __future__ import annotations

from typing import List, Literal
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.parlay_leg import ParlayLeg


ParlayStatus = Literal["PENDING", "LIVE", "WON", "LOST", "PUSH", "VOID"]


class ParlayStatusCalculator:
    """Calculate parlay status based on leg results.
    
    Multi-day / multi-event: each leg is independent. Parlay status changes ONLY when
    all legs are in a terminal state (WON/LOST/PUSH/VOID). Prevents early parlay settlement.
    """

    @staticmethod
    def calculate_status(legs: List[ParlayLeg]) -> ParlayStatus:
        """Calculate parlay status from leg results.
        
        Rules:
        - If any leg LOST → parlay LOST
        - If all legs WON or PUSH → parlay WON
        - If any leg LIVE and none lost → parlay LIVE
        - If any leg PENDING → parlay stays PENDING (no early settlement)
        - All legs must be resolved before parlay moves to WON/LOST/PUSH/VOID
        """
        if not legs:
            return "PENDING"
        
        leg_statuses = [leg.status for leg in legs]
        
        # If any leg is LOST, parlay is LOST
        if "LOST" in leg_statuses:
            return "LOST"
        
        # If any leg is VOID, check if all are VOID
        if "VOID" in leg_statuses:
            if all(status == "VOID" for status in leg_statuses):
                return "VOID"
            # Mixed VOID and other statuses - treat VOID as neutral for now
            # Could be refined based on business rules
        
        # If any leg is LIVE and none are LOST, parlay is LIVE
        if "LIVE" in leg_statuses:
            return "LIVE"
        
        # If any leg is PENDING, parlay is PENDING
        if "PENDING" in leg_statuses:
            return "PENDING"
        
        # All legs are settled (WON or PUSH)
        # If all are WON or PUSH, parlay is WON
        if all(status in ("WON", "PUSH") for status in leg_statuses):
            # If all are PUSH, could be PUSH depending on rules
            if all(status == "PUSH" for status in leg_statuses):
                return "PUSH"
            return "WON"
        
        # Fallback
        return "PENDING"
