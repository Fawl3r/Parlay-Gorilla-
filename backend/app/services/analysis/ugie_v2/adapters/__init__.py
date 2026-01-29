"""Sport-specific adapters to normalize matchup_data for UGIE v2 signals."""

from app.services.analysis.ugie_v2.adapters.base_adapter import (
    BaseUgieAdapter,
    NormalizedUgieInputs,
)
from app.services.analysis.ugie_v2.adapters.nfl_adapter import NflAdapter
from app.services.analysis.ugie_v2.adapters.mlb_adapter import MlBAdapter
from app.services.analysis.ugie_v2.adapters.soccer_adapter import SoccerAdapter

def get_adapter(sport: str) -> BaseUgieAdapter | None:
    """Return the adapter for the given sport, or None if not supported."""
    s = (sport or "").strip().lower()
    if s == "nfl":
        return NflAdapter()
    if s == "mlb":
        return MlBAdapter()
    if s == "soccer":
        return SoccerAdapter()
    return None


__all__ = [
    "BaseUgieAdapter",
    "NormalizedUgieInputs",
    "NflAdapter",
    "MlBAdapter",
    "SoccerAdapter",
    "get_adapter",
]
