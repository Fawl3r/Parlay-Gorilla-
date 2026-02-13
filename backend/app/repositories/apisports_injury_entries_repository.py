"""Per-player injury entries: upsert and query for analysis (player names + freshness)."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.apisports_injury_entry import ApisportsInjuryEntry


# Canonical status set for display
STATUS_MAP = {
    "out": "out",
    "questionable": "questionable",
    "doubtful": "doubtful",
    "probable": "probable",
    "day-to-day": "day-to-day",
    "gtd": "day-to-day",
}


def _normalize_status(raw: Optional[str]) -> str:
    if not raw:
        return "out"
    s = (raw or "").strip().lower().replace(" ", "-")
    return STATUS_MAP.get(s, s[:32] if len(s) > 32 else s)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ApisportsInjuryEntriesRepository:
    """Upsert and query per-player injury rows for UGIE availability + UI names."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def upsert_many(
        self,
        sport: str,
        apisports_team_id: int,
        injuries: List[Dict[str, Any]],
        fetched_at: datetime,
        league_id: Optional[int] = None,
    ) -> tuple[int, int]:
        """
        Insert or replace injury entries for a team (replace all for this team at this fetch time).
        Returns (stored_count, deduped_count). Dedupe by (sport, team_id, player_name, status, reported_at).
        """
        if not injuries:
            return 0, 0
        now = fetched_at if fetched_at.tzinfo else fetched_at.replace(tzinfo=timezone.utc)
        # Delete existing entries for this team with same fetched_at window (same run)
        await self._db.execute(
            delete(ApisportsInjuryEntry).where(
                ApisportsInjuryEntry.sport == sport,
                ApisportsInjuryEntry.apisports_team_id == apisports_team_id,
                ApisportsInjuryEntry.fetched_at >= now - timedelta(minutes=5),
            )
        )
        seen: set[tuple[str, str, Optional[datetime]]] = set()
        stored = 0
        for inj in injuries:
            name = (inj.get("player_name") or inj.get("name") or "Unknown").strip() or "Unknown"
            status = _normalize_status(inj.get("status") or inj.get("reason") or "out")
            reported = inj.get("reported_at")
            if isinstance(reported, str):
                try:
                    reported = datetime.fromisoformat(reported.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    reported = None
            key = (name, status, reported)
            if key in seen:
                continue
            seen.add(key)
            entry = ApisportsInjuryEntry(
                sport=sport,
                league_id=league_id,
                apisports_team_id=apisports_team_id,
                apisports_player_id=inj.get("apisports_player_id") or inj.get("player_id"),
                player_name=name,
                status=status,
                injury_type=(inj.get("injury_type") or inj.get("type") or "")[:128] or None,
                description=(inj.get("description") or inj.get("reason") or "")[:2000] or None,
                reported_at=reported,
                fetched_at=now,
                source="apisports",
                raw_payload=inj.get("raw_payload"),
            )
            self._db.add(entry)
            stored += 1
        await self._db.commit()
        return stored, len(injuries) - stored

    async def get_latest_for_teams(
        self,
        sport: str,
        team_ids: List[int],
        max_age_hours: int = 48,
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Return latest injury entries per team. Each list is sorted by reported_at desc.
        If newest fetched_at is older than max_age_hours, still return data but caller may set stale.
        """
        if not team_ids:
            return {}
        cutoff = _utc_now() - timedelta(hours=max_age_hours)
        result = await self._db.execute(
            select(ApisportsInjuryEntry)
            .where(
                ApisportsInjuryEntry.sport == sport,
                ApisportsInjuryEntry.apisports_team_id.in_(team_ids),
                ApisportsInjuryEntry.fetched_at >= cutoff,
            )
            .order_by(ApisportsInjuryEntry.apisports_team_id, ApisportsInjuryEntry.reported_at.desc().nullslast())
        )
        rows = result.scalars().all()
        by_team: Dict[int, List[Dict[str, Any]]] = {tid: [] for tid in team_ids}
        for r in rows:
            by_team.setdefault(r.apisports_team_id, []).append({
                "name": r.player_name,
                "status": r.status,
                "type": r.injury_type,
                "desc": r.description,
                "reported_at": r.reported_at.isoformat() if r.reported_at else None,
            })
        return by_team

    async def get_latest_summary_for_game(
        self,
        sport: str,
        home_team_id: int,
        away_team_id: int,
        max_age_hours: int = 48,
    ) -> Dict[str, Any]:
        """
        Combined structure for a game: home/away lists + last_updated_at.
        Keys: home, away, last_updated_at, stale (bool if newest fetched_at > max_age_hours).
        """
        by_team = await self.get_latest_for_teams(sport, [home_team_id, away_team_id], max_age_hours)
        home_list = by_team.get(home_team_id) or []
        away_list = by_team.get(away_team_id) or []
        # Latest fetched_at across these teams
        result = await self._db.execute(
            select(ApisportsInjuryEntry.fetched_at)
            .where(
                ApisportsInjuryEntry.sport == sport,
                ApisportsInjuryEntry.apisports_team_id.in_([home_team_id, away_team_id]),
            )
            .order_by(ApisportsInjuryEntry.fetched_at.desc())
            .limit(1)
        )
        latest_fetched = result.scalar_one_or_none()
        last_updated_at = latest_fetched.isoformat() if latest_fetched else None
        cutoff = _utc_now() - timedelta(hours=max_age_hours)
        stale = latest_fetched is None or latest_fetched < cutoff
        return {
            "home": home_list,
            "away": away_list,
            "last_updated_at": last_updated_at,
            "stale": stale,
        }
