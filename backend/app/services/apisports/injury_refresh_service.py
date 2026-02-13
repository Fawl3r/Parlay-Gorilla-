"""
Injury refresh: fetch and cache injuries per league/season, store by team + per-player entries. Quota-aware.

Called from SportsRefreshService / scheduler only. Uses get_injuries(league_id, season); groups by team_id.
Writes to apisports_injuries (blob) and apisports_injury_entries (player names for UI).
No live API from request path.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories.apisports_injury_repository import ApisportsInjuryRepository
from app.repositories.apisports_injury_entries_repository import ApisportsInjuryEntriesRepository
from app.services.apisports.client import get_apisports_client
from app.services.apisports.quota_manager import get_quota_manager
from app.services.apisports.season_resolver import get_season_int_for_sport

logger = logging.getLogger(__name__)


def _parse_item_to_entry(item: dict) -> dict[str, Any]:
    """Map API-Sports injury item to entry dict for upsert_many."""
    player = item.get("player") or {}
    name = (
        player.get("name")
        or (str(player.get("firstname", "")) + " " + str(player.get("lastname", ""))).strip()
        or "Unknown"
    )
    if isinstance(name, dict):
        name = name.get("name") or "Unknown"
    reason = item.get("reason") or item.get("type") or "Out"
    reported_at = item.get("date")
    if isinstance(reported_at, str) and reported_at:
        try:
            reported_at = datetime.fromisoformat(reported_at.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            reported_at = None
    return {
        "player_name": str(name).strip() or "Unknown",
        "status": reason,
        "injury_type": item.get("type"),
        "description": reason,
        "reported_at": reported_at,
        "apisports_player_id": player.get("id") if isinstance(player, dict) else None,
        "raw_payload": item,
    }


class InjuryRefreshService:
    """
    Refresh injuries for (sport, league_id, season). One API call; upsert per team.
    TTL-skip if all teams fresh; respects quota reserve.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = ApisportsInjuryRepository(db)
        self._entries_repo = ApisportsInjuryEntriesRepository(db)
        self._client = get_apisports_client()
        self._quota = get_quota_manager()

    def _reserve(self) -> int:
        return getattr(settings, "apisports_budget_reserve", 5)

    def _ttl_seconds(self) -> int:
        return getattr(settings, "apisports_ttl_injuries_seconds", 21600)

    async def refresh_injuries(
        self,
        sport: str,
        league_id: int,
        season: str,
    ) -> dict[str, Any]:
        """
        Call API-Sports get_injuries(league_id, season); group by team_id; upsert blob + per-player entries.
        Returns summary: provider_calls=1, teams_covered, records_written (entry count).
        """
        if not self._client.is_configured():
            return {"provider_calls": 0, "teams_covered": 0, "records_written": 0}

        reserve = self._reserve()
        if await self._quota.remaining_async(sport) <= reserve:
            logger.debug("InjuryRefresh: skip (quota <= reserve)")
            return {"provider_calls": 0, "teams_covered": 0, "records_written": 0}

        try:
            season_int = int(season.split("-")[0]) if season and "-" in season else int(season or "0")
        except (TypeError, ValueError):
            season_int = get_season_int_for_sport(sport)

        data = await self._client.get_injuries(
            league_id=league_id,
            season=season_int,
            sport=sport,
        )
        if not data or not isinstance(data.get("response"), list):
            return {"provider_calls": 1, "teams_covered": 0, "records_written": 0}

        by_team: dict[int, List[dict[str, Any]]] = defaultdict(list)
        for item in data["response"]:
            if not isinstance(item, dict):
                continue
            team = item.get("team")
            if isinstance(team, dict) and team.get("id") is not None:
                tid = int(team["id"])
                by_team[tid].append(item)
            elif isinstance(team, (int, float)):
                tid = int(team)
                by_team[tid].append(item)

        ttl = self._ttl_seconds()
        fetched_at = datetime.now(timezone.utc)
        teams_covered = 0
        records_written = 0
        for team_id, payload_list in by_team.items():
            if await self._quota.remaining_async(sport) <= reserve:
                break
            payload = {"response": payload_list}
            await self._repo.upsert_team_injury(
                sport=sport,
                league_id=league_id,
                team_id=team_id,
                payload=payload,
                stale_after_seconds=ttl,
            )
            teams_covered += 1
            entries = [_parse_item_to_entry(it) for it in payload_list]
            stored, _ = await self._entries_repo.upsert_many(
                sport=sport,
                apisports_team_id=team_id,
                injuries=entries,
                fetched_at=fetched_at,
                league_id=league_id,
            )
            records_written += stored

        if teams_covered:
            logger.info(
                "InjuryRefreshService: refreshed injuries for %s league %s (%s teams, %s entries)",
                sport, league_id, teams_covered, records_written,
            )
        return {"provider_calls": 1, "teams_covered": teams_covered, "records_written": records_written}
