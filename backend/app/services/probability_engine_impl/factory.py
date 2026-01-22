from __future__ import annotations

from typing import Dict, Optional, Type

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.probability_engine_impl.base_engine import BaseProbabilityEngine
from app.services.probability_engine_impl.engines import (
    GenericProbabilityEngine,
    MLBProbabilityEngine,
    NBAProbabilityEngine,
    NFLProbabilityEngine,
    NHLProbabilityEngine,
    SoccerProbabilityEngine,
)


ENGINE_CLASS_MAP: Dict[str, Type[BaseProbabilityEngine]] = {
    "nfl": NFLProbabilityEngine,
    "americanfootball_nfl": NFLProbabilityEngine,
    "nba": NBAProbabilityEngine,
    "basketball_nba": NBAProbabilityEngine,
    "nhl": NHLProbabilityEngine,
    "icehockey_nhl": NHLProbabilityEngine,
    "mlb": MLBProbabilityEngine,
    "baseball_mlb": MLBProbabilityEngine,
    "ncaab": NBAProbabilityEngine,
    "basketball_ncaab": NBAProbabilityEngine,
    "ncaaf": NFLProbabilityEngine,
    "americanfootball_ncaaf": NFLProbabilityEngine,
    "soccer": SoccerProbabilityEngine,
    "soccer_epl": SoccerProbabilityEngine,
    "soccer_mls": SoccerProbabilityEngine,
    "soccer_usa_mls": SoccerProbabilityEngine,
    "ufc": GenericProbabilityEngine,
    "mma": GenericProbabilityEngine,
    "mma_mixed_martial_arts": GenericProbabilityEngine,
    "boxing": GenericProbabilityEngine,
    "boxing_boxing": GenericProbabilityEngine,
}


def get_probability_engine(db: AsyncSession, sport: Optional[str] = None) -> BaseProbabilityEngine:
    """Factory returning an engine tuned for the requested sport."""
    key = (sport or "nfl").lower()
    engine_cls = ENGINE_CLASS_MAP.get(key, NFLProbabilityEngine)
    return engine_cls(db)


