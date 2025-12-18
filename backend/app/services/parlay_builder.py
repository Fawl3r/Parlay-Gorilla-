"""Parlay builder public API.

This module is a thin public wrapper around the implementation in
`app.services.parlay_builder_impl.parlay_builder_service`, kept small to comply
with the repo rule that no file should exceed 500 lines.
"""

from app.services.parlay_builder_impl.parlay_builder_service import ParlayBuilderService
from app.services.probability_engine import get_probability_engine

__all__ = ["ParlayBuilderService", "get_probability_engine"]


