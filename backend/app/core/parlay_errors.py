"""
Domain exceptions for parlay generation.

Use these instead of broad ValueError so the API can return 409
for insufficient candidates and let other errors bubble as 500.
"""


class InsufficientCandidatesException(Exception):
    """Raised when the builder cannot fulfill requested legs with available candidates."""

    def __init__(self, needed: int, have: int, message: str = ""):
        self.needed = needed
        self.have = have
        super().__init__(message or f"Not enough candidates: need {needed}, have {have}")
