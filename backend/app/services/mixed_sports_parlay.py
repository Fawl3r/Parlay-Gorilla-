"""Mixed sports parlay builder public API.

This module is a thin wrapper around the implementation in
`app.services.mixed_sports_parlay_impl`, kept small to comply with the repo rule
that no file should exceed 500 lines.
"""

from app.services.mixed_sports_parlay_impl.mixed_sports_parlay_builder import (
    MixedSportsParlayBuilder,
    build_mixed_sports_parlay,
)

__all__ = ["MixedSportsParlayBuilder", "build_mixed_sports_parlay"]





