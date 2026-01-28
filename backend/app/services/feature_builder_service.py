"""
Feature builder: compute derived features from API-Sports + internal data.

Stores to apisports_features: form, rest days, home/away splits, opponent strength proxy.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.apisports_feature import ApisportsFeature
from app.models.apisports_fixture import ApisportsFixture
from app.models.apisports_result import ApisportsResult
from app.models.apisports_standing import ApisportsStanding
from app.models.apisports_team_stat import ApisportsTeamStat

logger = logging.getLogger(__name__)


class FeatureBuilderService:
    """Builds and persists derived features for modeling (form, rest days, splits, opponent strength)."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def build_team_features(
        self,
        sport: str,
        team_id: int,
        league_id: Optional[int] = None,
        season: Optional[str] = None,
        last_n: int = 5,
    ) -> Optional[Dict[str, Any]]:
        """
        Compute features for a team: last N form, home/away split, rest days, opponent strength proxy.
        Persist to apisports_features and return features dict.
        """
        # Load recent results for this team
        home_results = await self._db.execute(
            select(ApisportsResult).where(
                ApisportsResult.sport == sport,
                ApisportsResult.home_team_id == team_id,
            ).order_by(ApisportsResult.finished_at.desc().nullslast()).limit(last_n * 2)
        )
        away_results = await self._db.execute(
            select(ApisportsResult).where(
                ApisportsResult.sport == sport,
                ApisportsResult.away_team_id == team_id,
            ).order_by(ApisportsResult.finished_at.desc().nullslast()).limit(last_n * 2)
        )
        home_rows = list(home_results.scalars().all())
        away_rows = list(away_results.scalars().all())

        wins = 0
        losses = 0
        home_wins, home_losses = 0, 0
        away_wins, away_losses = 0, 0
        last_finished: Optional[datetime] = None
        games_used: List[Dict[str, Any]] = []

        for row in home_rows[:last_n]:
            if row.home_score is not None and row.away_score is not None:
                if row.home_score > row.away_score:
                    wins += 1
                    home_wins += 1
                else:
                    losses += 1
                    home_losses += 1
                if row.finished_at:
                    last_finished = row.finished_at
                games_used.append({"venue": "home", "finished_at": row.finished_at})

        for row in away_rows[:last_n]:
            if row.home_score is not None and row.away_score is not None:
                if row.away_score > row.home_score:
                    wins += 1
                    away_wins += 1
                else:
                    losses += 1
                    away_losses += 1
                if row.finished_at:
                    last_finished = row.finished_at
                games_used.append({"venue": "away", "finished_at": row.finished_at})

        # Rest days: days since last game (simplified: 0 if no last_finished)
        rest_days: Optional[int] = None
        if last_finished:
            delta = (datetime.now(timezone.utc) - last_finished.replace(tzinfo=timezone.utc)).days
            rest_days = max(0, delta)

        # Opponent strength proxy: use standings rank if available
        opponent_strength_proxy: Optional[float] = None
        standings_result = await self._db.execute(
            select(ApisportsStanding).where(
                ApisportsStanding.sport == sport,
                ApisportsStanding.league_id == league_id,
            ).limit(1)
        )
        standing_row = standings_result.scalar_one_or_none()
        if standing_row and isinstance(standing_row.payload_json, dict):
            # Placeholder: could parse standings and find team rank
            opponent_strength_proxy = 0.5

        features_json: Dict[str, Any] = {
            "last_n_form_wins": wins,
            "last_n_form_losses": losses,
            "last_n": last_n,
            "home_wins": home_wins,
            "home_losses": home_losses,
            "away_wins": away_wins,
            "away_losses": away_losses,
            "rest_days": rest_days,
            "games_used": len(games_used),
        }
        home_away_split = {
            "home_wins": home_wins,
            "home_losses": home_losses,
            "away_wins": away_wins,
            "away_losses": away_losses,
        }

        # Upsert apisports_features
        existing = await self._db.execute(
            select(ApisportsFeature).where(
                ApisportsFeature.sport == sport,
                ApisportsFeature.team_id == team_id,
            )
        )
        row = existing.scalar_one_or_none()
        now = datetime.now(timezone.utc)
        if row:
            row.features_json = features_json
            row.last_n_form_wins = wins
            row.last_n_form_losses = losses
            row.rest_days = rest_days
            row.home_away_split_json = home_away_split
            row.opponent_strength_proxy = opponent_strength_proxy
            row.updated_at = now
        else:
            row = ApisportsFeature(
                sport=sport,
                team_id=team_id,
                league_id=league_id,
                season=season,
                features_json=features_json,
                last_n_form_wins=wins,
                last_n_form_losses=losses,
                rest_days=rest_days,
                home_away_split_json=home_away_split,
                opponent_strength_proxy=opponent_strength_proxy,
            )
            self._db.add(row)
        await self._db.commit()
        return features_json
