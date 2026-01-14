"""ESPN scoreboard sync service for populating game_results table.

This service fetches completed games from ESPN scoreboard endpoints and upserts
them into the game_results table. Used by the background scheduler to keep
recent game results available for parlay grading.
"""

from __future__ import annotations

import httpx
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game_results import GameResult
from app.utils.timezone_utils import TimezoneNormalizer

logger = logging.getLogger(__name__)


class EspnGameResultsSyncService:
    """Sync completed game results from ESPN scoreboard to game_results table."""

    ESPN_BASE_URLS = {
        "NFL": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
        "NBA": "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",
        "NHL": "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard",
        "MLB": "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard",
        "NCAAF": "https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard",
        "NCAAB": "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard",
        "MLS": "https://site.api.espn.com/apis/site/v2/sports/soccer/usa.1/scoreboard",
        "EPL": "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard",
        "LALIGA": "https://site.api.espn.com/apis/site/v2/sports/soccer/esp.1/scoreboard",
        "UCL": "https://site.api.espn.com/apis/site/v2/sports/soccer/uefa.champions/scoreboard",
        "SOCCER": "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard",
    }

    TIMEOUT = 10.0

    def __init__(self, db: AsyncSession):
        self.db = db

    async def sync_recent_games(self, *, lookback_days: int = 3) -> int:
        """
        Sync completed games from ESPN for the last N days.

        Args:
            lookback_days: Number of days to look back (default 3)

        Returns:
            Number of games synced (new or updated)
        """
        now = datetime.now(timezone.utc)
        synced_count = 0

        for sport_code, base_url in self.ESPN_BASE_URLS.items():
            try:
                for offset in range(lookback_days + 1):
                    target_date = (now.date() - timedelta(days=offset))
                    count = await self._sync_date(sport_code=sport_code, target_date=target_date, base_url=base_url)
                    synced_count += count
            except Exception as e:
                logger.warning(f"[GAME_RESULTS_SYNC] Error syncing {sport_code}: {e}")
                continue

        return synced_count

    async def _sync_date(self, *, sport_code: str, target_date: date, base_url: str) -> int:
        """Sync games for a specific date and sport."""
        date_str = target_date.strftime("%Y%m%d")
        url = f"{base_url}?dates={date_str}"

        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                response = await client.get(url)
                if response.status_code != 200:
                    logger.debug(f"[GAME_RESULTS_SYNC] ESPN returned {response.status_code} for {sport_code} on {date_str}")
                    return 0

                data = response.json()
                events = data.get("events", [])
                if not events:
                    return 0

                synced = 0
                for event in events:
                    try:
                        if await self._upsert_game_result(sport_code=sport_code, event=event):
                            synced += 1
                    except Exception as e:
                        logger.debug(f"[GAME_RESULTS_SYNC] Error processing event {event.get('id')}: {e}")
                        continue

                return synced
        except httpx.TimeoutException:
            logger.warning(f"[GAME_RESULTS_SYNC] ESPN timeout for {sport_code} on {date_str}")
            return 0
        except Exception as e:
            logger.error(f"[GAME_RESULTS_SYNC] ESPN error for {sport_code} on {date_str}: {e}")
            return 0

    async def _upsert_game_result(self, *, sport_code: str, event: Dict) -> bool:
        """Upsert a single game result from ESPN event data."""
        event_id = str(event.get("id") or "").strip()
        if not event_id:
            return False

        competitions = event.get("competitions", [])
        if not competitions:
            return False

        comp = competitions[0]
        status = comp.get("status", {})
        status_type = status.get("type", {})

        # Only process completed games
        if not status_type.get("completed", False):
            return False

        competitors = comp.get("competitors", [])
        if len(competitors) < 2:
            return False

        # Find home and away
        home_comp = next((c for c in competitors if c.get("homeAway") == "home"), None)
        away_comp = next((c for c in competitors if c.get("homeAway") == "away"), None)

        if not home_comp or not away_comp:
            return False

        home_team = home_comp.get("team", {}).get("displayName", "").strip()
        away_team = away_comp.get("team", {}).get("displayName", "").strip()

        if not home_team or not away_team:
            return False

        # Parse scores
        home_score_raw = home_comp.get("score", "")
        away_score_raw = away_comp.get("score", "")

        try:
            home_score = int(home_score_raw) if home_score_raw else None
            away_score = int(away_score_raw) if away_score_raw else None
        except (ValueError, TypeError):
            home_score = None
            away_score = None

        if home_score is None or away_score is None:
            return False

        # Parse game date
        date_str_raw = comp.get("date", "")
        game_date = None
        if date_str_raw:
            try:
                dt = datetime.fromisoformat(date_str_raw.replace("Z", "+00:00"))
                game_date = TimezoneNormalizer.ensure_utc(dt)
            except Exception:
                logger.debug(f"[GAME_RESULTS_SYNC] Failed to parse date {date_str_raw}")
                return False

        if not game_date:
            return False

        # Build external_game_id (ESPN format)
        external_game_id = f"espn:{sport_code.lower()}:{event_id}"

        # Check if already exists
        result = await self.db.execute(
            select(GameResult).where(GameResult.external_game_id == external_game_id).limit(1)
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update scores if different
            if existing.home_score != home_score or existing.away_score != away_score:
                existing.home_score = home_score
                existing.away_score = away_score
                existing.actual_total = home_score + away_score
                existing.updated_at = datetime.now(timezone.utc)
                await self.db.commit()
                return True
            return False

        # Create new record
        winner = "home" if home_score > away_score else ("away" if away_score > home_score else None)

        new_result = GameResult(
            external_game_id=external_game_id,
            sport=sport_code,
            home_team=home_team,
            away_team=away_team,
            game_date=game_date,
            home_score=home_score,
            away_score=away_score,
            actual_total=home_score + away_score,
            winner=winner,
            status="final",
            completed="true",
        )

        self.db.add(new_result)
        await self.db.commit()
        return True

