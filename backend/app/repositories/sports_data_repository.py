"""
Sports data repository: DB-first read/write for API-Sports cache.

All reads used by user-facing endpoints must hit DB only (no live API calls).
Freshness: is_fresh(entity, stale_after_seconds), last_fetched_at.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, List, Optional

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.apisports_fixture import ApisportsFixture
from app.models.apisports_result import ApisportsResult
from app.models.apisports_standing import ApisportsStanding
from app.models.apisports_team_stat import ApisportsTeamStat

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SportsDataRepository:
    """Read/write fixtures, results, team stats, standings. Freshness checks via last_fetched_at."""

    def __init__(self, db: AsyncSession):
        self._db = db

    @staticmethod
    def is_fresh(last_fetched_at: Optional[datetime], stale_after_seconds: Optional[int]) -> bool:
        """Return True if entity is still fresh (not past stale_after_seconds)."""
        if last_fetched_at is None:
            return False
        if stale_after_seconds is None or stale_after_seconds <= 0:
            return True
        delta = (_utc_now() - last_fetched_at).total_seconds()
        return delta < stale_after_seconds

    # ---------- Fixtures ----------

    async def upsert_fixtures(
        self,
        sport: str,
        fixtures: List[dict[str, Any]],
        source: str = "api_sports",
        stale_after_seconds: Optional[int] = None,
    ) -> int:
        """Upsert fixture rows. Expects list of dicts with fixture_id, date, home_team_id, away_team_id, league_id, payload_json."""
        if not fixtures:
            return 0
        now = _utc_now()
        count = 0
        for f in fixtures:
            # API-Sports format: { "fixture": { "id", "date" }, "league": { "id" }, "teams": { "home": { "id" }, "away": { "id" } } }
            fixture_obj = f.get("fixture") if isinstance(f.get("fixture"), dict) else {}
            league_obj = f.get("league") if isinstance(f.get("league"), dict) else {}
            teams_obj = f.get("teams") if isinstance(f.get("teams"), dict) else {}
            fixture_id = fixture_obj.get("id") or f.get("fixture_id") or f.get("id")
            if fixture_id is None:
                continue
            league_id = league_obj.get("id") or f.get("league_id")
            date_val = fixture_obj.get("date") or f.get("date")
            home_team_id = None
            away_team_id = None
            if teams_obj:
                home_team_id = teams_obj.get("home", {}).get("id") if isinstance(teams_obj.get("home"), dict) else None
                away_team_id = teams_obj.get("away", {}).get("id") if isinstance(teams_obj.get("away"), dict) else None
            payload = f  # store raw for debugging

            existing = await self._db.execute(
                select(ApisportsFixture).where(
                    ApisportsFixture.sport == sport,
                    ApisportsFixture.fixture_id == fixture_id,
                )
            )
            row = existing.scalar_one_or_none()
            if row:
                row.payload_json = payload
                row.last_fetched_at = now
                row.stale_after_seconds = stale_after_seconds
                row.league_id = league_id
                row.home_team_id = home_team_id
                row.away_team_id = away_team_id
                row.updated_at = now
            else:
                row = ApisportsFixture(
                    sport=sport,
                    league_id=league_id,
                    fixture_id=fixture_id,
                    date=date_val,
                    home_team_id=home_team_id,
                    away_team_id=away_team_id,
                    payload_json=payload,
                    source=source,
                    last_fetched_at=now,
                    stale_after_seconds=stale_after_seconds,
                )
                self._db.add(row)
            count += 1
        await self._db.commit()
        return count

    async def get_fixtures(
        self,
        sport: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        league_id: Optional[int] = None,
    ) -> List[ApisportsFixture]:
        """Return fixtures for sport in date range (and optional league)."""
        q = select(ApisportsFixture).where(ApisportsFixture.sport == sport)
        if from_date is not None:
            q = q.where(ApisportsFixture.date >= from_date)
        if to_date is not None:
            q = q.where(ApisportsFixture.date <= to_date)
        if league_id is not None:
            q = q.where(ApisportsFixture.league_id == league_id)
        q = q.order_by(ApisportsFixture.date)
        result = await self._db.execute(q)
        return list(result.scalars().all())

    # ---------- Team stats ----------

    async def upsert_team_stats(
        self,
        sport: str,
        team_id: int,
        stats: dict[str, Any],
        league_id: Optional[int] = None,
        season: Optional[str] = None,
        source: str = "api_sports",
        stale_after_seconds: Optional[int] = None,
    ) -> None:
        """Upsert one team stats row (by sport + team_id; overwrite latest)."""
        now = _utc_now()
        existing = await self._db.execute(
            select(ApisportsTeamStat).where(
                ApisportsTeamStat.sport == sport,
                ApisportsTeamStat.team_id == team_id,
            )
        )
        row = existing.scalar_one_or_none()
        if row:
            row.payload_json = stats
            row.last_fetched_at = now
            row.stale_after_seconds = stale_after_seconds
            row.league_id = league_id
            row.season = season
            row.updated_at = now
        else:
            row = ApisportsTeamStat(
                sport=sport,
                league_id=league_id,
                team_id=team_id,
                season=season,
                payload_json=stats,
                source=source,
                last_fetched_at=now,
                stale_after_seconds=stale_after_seconds,
            )
            self._db.add(row)
        await self._db.commit()

    async def get_team_stats(
        self,
        sport: str,
        team_id: int,
    ) -> Optional[ApisportsTeamStat]:
        """Return latest team stats for sport/team_id."""
        result = await self._db.execute(
            select(ApisportsTeamStat).where(
                ApisportsTeamStat.sport == sport,
                ApisportsTeamStat.team_id == team_id,
            ).order_by(ApisportsTeamStat.last_fetched_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    # ---------- Standings ----------

    async def upsert_standings(
        self,
        sport: str,
        league_id: int,
        standings: dict[str, Any],
        season: Optional[str] = None,
        source: str = "api_sports",
        stale_after_seconds: Optional[int] = None,
    ) -> None:
        """Upsert standings for sport/league (overwrite)."""
        now = _utc_now()
        existing = await self._db.execute(
            select(ApisportsStanding).where(
                ApisportsStanding.sport == sport,
                ApisportsStanding.league_id == league_id,
            )
        )
        row = existing.scalar_one_or_none()
        if row:
            row.payload_json = standings
            row.last_fetched_at = now
            row.stale_after_seconds = stale_after_seconds
            row.season = season
            row.updated_at = now
        else:
            row = ApisportsStanding(
                sport=sport,
                league_id=league_id,
                season=season,
                payload_json=standings,
                source=source,
                last_fetched_at=now,
                stale_after_seconds=stale_after_seconds,
            )
            self._db.add(row)
        await self._db.commit()

    async def get_standings(
        self,
        sport: str,
        league_id: Optional[int] = None,
    ) -> List[ApisportsStanding]:
        """Return standings for sport (and optional league_id)."""
        q = select(ApisportsStanding).where(ApisportsStanding.sport == sport)
        if league_id is not None:
            q = q.where(ApisportsStanding.league_id == league_id)
        result = await self._db.execute(q)
        return list(result.scalars().all())

    # ---------- Results ----------

    async def upsert_results(
        self,
        sport: str,
        results: List[dict[str, Any]],
        source: str = "api_sports",
        stale_after_seconds: Optional[int] = None,
    ) -> int:
        """Upsert result rows. Expects list of dicts with fixture_id, home_score, away_score, finished_at, etc."""
        if not results:
            return 0
        now = _utc_now()
        count = 0
        for r in results:
            # API-Sports format: { "fixture": { "id", "date" }, "teams": { "home": { "id" }, "away": { "id" } }, "score": { "fulltime": { "home", "away" } } }
            fixture_obj = r.get("fixture", {}) if isinstance(r.get("fixture"), dict) else {}
            teams_obj = r.get("teams", {}) if isinstance(r.get("teams"), dict) else {}
            score_obj = r.get("score", {}) if isinstance(r.get("score"), dict) else {}
            
            fixture_id = fixture_obj.get("id") or r.get("fixture_id") or r.get("id")
            if fixture_id is None:
                continue
            
            league_id = r.get("league_id") or (r.get("league", {}).get("id") if isinstance(r.get("league"), dict) else None)
            
            home_team_id = None
            away_team_id = None
            if teams_obj:
                home_team_id = teams_obj.get("home", {}).get("id") if isinstance(teams_obj.get("home"), dict) else None
                away_team_id = teams_obj.get("away", {}).get("id") if isinstance(teams_obj.get("away"), dict) else None
            
            # Extract scores
            fulltime_score = score_obj.get("fulltime", {}) if isinstance(score_obj.get("fulltime"), dict) else {}
            home_score = fulltime_score.get("home") or score_obj.get("home", None)
            away_score = fulltime_score.get("away") or score_obj.get("away", None)
            
            # Extract finish time
            date_str = fixture_obj.get("date") or r.get("date")
            finished_at = None
            if date_str:
                try:
                    finished_at = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except Exception:
                    pass
            
            payload = r  # store raw for debugging
            
            existing = await self._db.execute(
                select(ApisportsResult).where(
                    ApisportsResult.sport == sport,
                    ApisportsResult.fixture_id == fixture_id,
                )
            )
            row = existing.scalar_one_or_none()
            if row:
                row.payload_json = payload
                row.home_score = home_score
                row.away_score = away_score
                row.finished_at = finished_at
                row.last_fetched_at = now
                row.league_id = league_id
                row.home_team_id = home_team_id
                row.away_team_id = away_team_id
                row.updated_at = now
            else:
                row = ApisportsResult(
                    sport=sport,
                    league_id=league_id,
                    fixture_id=fixture_id,
                    home_team_id=home_team_id,
                    away_team_id=away_team_id,
                    home_score=home_score,
                    away_score=away_score,
                    finished_at=finished_at,
                    payload_json=payload,
                    source=source,
                    last_fetched_at=now,
                )
                self._db.add(row)
            count += 1
        await self._db.commit()
        return count

    async def get_results(
        self,
        sport: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        league_id: Optional[int] = None,
        team_id: Optional[int] = None,
    ) -> List[ApisportsResult]:
        """Return completed game results for sport in date range (and optional league/team)."""
        q = select(ApisportsResult).where(ApisportsResult.sport == sport)
        if from_date is not None:
            q = q.where(ApisportsResult.finished_at >= from_date)
        if to_date is not None:
            q = q.where(ApisportsResult.finished_at <= to_date)
        if league_id is not None:
            q = q.where(ApisportsResult.league_id == league_id)
        if team_id is not None:
            q = q.where(
                (ApisportsResult.home_team_id == team_id) | (ApisportsResult.away_team_id == team_id)
            )
        q = q.order_by(ApisportsResult.finished_at.desc())
        result = await self._db.execute(q)
        return list(result.scalars().all())
