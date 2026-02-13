"""
Resolve team name to API-Sports team_id: DB first, then in-memory mapper, then fuzzy DB.

Used by RosterContextBuilder and any async path that has a DB session.
Persists mappings to in-memory cache when found from DB so sync callers benefit.
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.apisports_team_repository import ApisportsTeamRepository
from app.services.apisports.team_mapper import get_team_mapper
from app.services.team_name_normalizer import TeamNameNormalizer

logger = logging.getLogger(__name__)


async def resolve_team_id_async(
    db: AsyncSession,
    team_name: str,
    sport: str,
    league_id: Optional[int] = None,
) -> Optional[int]:
    """
    Resolve team name to API-Sports team_id. Checks DB first, then in-memory mapper, then fuzzy DB.
    When found from DB, updates in-memory mapper so sync callers benefit next time.
    """
    if not (team_name and sport):
        return None
    normalizer = TeamNameNormalizer()
    mapper = get_team_mapper()
    sport_key = mapper._normalize_sport_key(sport)
    normalized = normalizer.normalize(team_name, sport=sport)
    if not normalized:
        return None

    repo = ApisportsTeamRepository(db)

    tid = await repo.find_team_id_by_name(sport_key, normalized, league_id=league_id)
    if tid is not None:
        mapper.add_mapping(team_name, tid, sport)
        return tid

    tid = mapper.get_team_id(team_name, sport, league_id=league_id)
    if tid is not None:
        return tid

    tid = await repo.find_team_id_by_name_fuzzy(sport_key, normalized, league_id=league_id)
    if tid is not None:
        mapper.add_mapping(team_name, tid, sport)
        logger.debug("resolve_team_id_async: fuzzy match '%s' -> %s for %s", team_name, tid, sport_key)
        return tid

    return None
