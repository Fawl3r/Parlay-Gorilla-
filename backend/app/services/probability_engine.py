"""Probability calculation engine for parlay building.

This module is a thin public wrapper around the implementation in
`app.services.probability_engine_impl`, kept small to comply with the repo rule
that no file should exceed 500 lines.
"""

from app.services.probability_engine_impl.base_engine import BaseProbabilityEngine
from app.services.probability_engine_impl.engines import (
    GenericProbabilityEngine,
    MLBProbabilityEngine,
    NBAProbabilityEngine,
    NFLProbabilityEngine,
    NHLProbabilityEngine,
    SoccerProbabilityEngine,
    WNBAProbabilityEngine,
)
from app.services.probability_engine_impl.factory import ENGINE_CLASS_MAP, get_probability_engine

# Backwards compatibility (legacy imports expect ProbabilityEngine to be NFL).
ProbabilityEngine = NFLProbabilityEngine

__all__ = [
    "BaseProbabilityEngine",
    "GenericProbabilityEngine",
    "NFLProbabilityEngine",
    "NBAProbabilityEngine",
    "NHLProbabilityEngine",
    "MLBProbabilityEngine",
    "SoccerProbabilityEngine",
    "WNBAProbabilityEngine",
    "ENGINE_CLASS_MAP",
    "get_probability_engine",
    "ProbabilityEngine",
]


