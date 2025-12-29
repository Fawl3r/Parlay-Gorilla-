from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game_results import GameResult
from app.services.team_name_normalizer import TeamNameNormalizer
from app.utils.timezone_utils import TimezoneNormalizer


@dataclass(frozen=True)
class GameResultLookupConfig:
    window_hours: int = 36
    max_candidates: int = 50


class GameResultLookupService:
    """
    Find the best matching `GameResult` row for a given matchup.

    We intentionally do conservative matching:
    - Match by sport (exact)
    - Match by normalized home/away names
    - Match by game_date within a time window around start_time (when provided)
    """

    def __init__(
        self,
        db: AsyncSession,
        *,
        config: Optional[GameResultLookupConfig] = None,
        normalizer: Optional[TeamNameNormalizer] = None,
    ):
        self._db = db
        self._cfg = config or GameResultLookupConfig()
        self._normalizer = normalizer or TeamNameNormalizer()

    async def find_best(
        self,
        *,
        sport: str,
        home_team: str,
        away_team: str,
        start_time: Optional[datetime] = None,
    ) -> Optional[GameResult]:
        sport_code = str(sport or "").upper().strip()
        if not sport_code:
            return None

        home_norm = self._normalizer.normalize(home_team)
        away_norm = self._normalizer.normalize(away_team)
        if not home_norm or not away_norm:
            return None

        candidates = await self._load_candidates(sport=sport_code, start_time=start_time)
        if not candidates:
            return None

        best: Optional[GameResult] = None
        best_score: float = 1e18

        target_time = TimezoneNormalizer.ensure_utc(start_time) if start_time else None
        for gr in candidates:
            gr_home = self._normalizer.normalize(getattr(gr, "home_team", "") or "")
            gr_away = self._normalizer.normalize(getattr(gr, "away_team", "") or "")

            if not gr_home or not gr_away:
                continue

            # Score: lower is better.
            # 0 = perfect home/away match; 1000 penalty for swapped match; reject otherwise.
            if gr_home == home_norm and gr_away == away_norm:
                penalty = 0.0
            elif gr_home == away_norm and gr_away == home_norm:
                penalty = 1000.0
            else:
                continue

            time_penalty = 0.0
            if target_time and getattr(gr, "game_date", None):
                gr_time = TimezoneNormalizer.ensure_utc(gr.game_date)
                time_penalty = abs((gr_time - target_time).total_seconds())

            score = penalty + time_penalty
            if score < best_score:
                best_score = score
                best = gr

        return best

    async def _load_candidates(self, *, sport: str, start_time: Optional[datetime]) -> list[GameResult]:
        query = select(GameResult).where(GameResult.sport == sport)

        if start_time:
            st = TimezoneNormalizer.ensure_utc(start_time)
            window = timedelta(hours=max(1, int(self._cfg.window_hours)))
            start = st - window
            end = st + window
            query = query.where(GameResult.game_date >= start).where(GameResult.game_date <= end)
        else:
            # Fallback: only consider recent results if we don't have a start time.
            now = datetime.now(timezone.utc)
            query = query.where(GameResult.game_date >= now - timedelta(days=14))

        # Only completed games with scores.
        query = (
            query.where(GameResult.completed == "true")
            .where(GameResult.home_score.isnot(None))
            .where(GameResult.away_score.isnot(None))
            .order_by(GameResult.game_date.desc())
            .limit(int(self._cfg.max_candidates))
        )

        res = await self._db.execute(query)
        return list(res.scalars().all())


