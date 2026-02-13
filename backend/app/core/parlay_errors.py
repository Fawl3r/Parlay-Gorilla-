"""
Domain exceptions for parlay generation.

Use these instead of broad ValueError so the API can return 409
for insufficient candidates and let other errors bubble as 500.
Single-point telemetry: record_insufficient_and_raise() increments
not_enough_games_failures_30m in exactly one place (service-level).
"""


class InsufficientCandidatesException(Exception):
    """Raised when the builder cannot fulfill requested legs with available candidates."""

    def __init__(self, needed: int, have: int, message: str = ""):
        self.needed = needed
        self.have = have
        super().__init__(message or f"Not enough candidates: need {needed}, have {have}")


def record_insufficient_and_raise(needed: int, have: int, message: str = "") -> None:
    """Increment not_enough_games_failures_30m once and raise InsufficientCandidatesException."""
    from app.core import telemetry
    telemetry.inc("not_enough_games_failures_30m")
    raise InsufficientCandidatesException(needed=needed, have=have, message=message)
