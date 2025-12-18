from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.game import Game
from app.models.market import Market
from app.services.odds_history.odds_history_snapshot_repository import OddsHistorySnapshotRepository
from app.services.odds_history.odds_movement_service import OddsMovementService
from app.services.odds_snapshot_builder import OddsSnapshotBuilder
from app.services.sports_config import get_sport_config
from app.services.probability_engine_impl.external_data_repository import ExternalDataRepository
from app.utils.nfl_week import get_week_date_range, get_current_nfl_week


class CandidateLegService:
    """Builds candidate legs for parlay generation."""

    def __init__(self, engine: "BaseProbabilityEngine", repo: ExternalDataRepository):
        self._engine = engine
        self._repo = repo
        self._odds_snapshot_builder = OddsSnapshotBuilder()
        self._odds_history_repo = OddsHistorySnapshotRepository(engine.db)
        self._odds_movement = OddsMovementService()

    async def get_candidate_legs(
        self,
        sport: Optional[str],
        min_confidence: float,
        max_legs: int,
        week: Optional[int],
    ) -> List[Dict]:
        target_sport = (sport or getattr(self._engine, "sport_code", None) or "NFL").upper()
        cutoff_time, future_cutoff = self._resolve_date_range(target_sport, week)

        # Hard cap how many games we even load from the DB. This prevents slow
        # queries and huge relationship loads when the table has accumulated
        # many scheduled games (or when game times/statuses drift).
        max_games_to_process = max(1, int(settings.probability_prefetch_max_games))

        result = await self._engine.db.execute(
            select(Game)
            .where(Game.sport == target_sport)
            .where(Game.start_time >= cutoff_time)
            .where(Game.start_time <= future_cutoff)
            .where(Game.status == "scheduled")
            .order_by(Game.start_time)
            .limit(max_games_to_process)
            .options(selectinload(Game.markets).selectinload(Market.odds))
        )
        games_to_process = result.scalars().all()

        # Prefetch auxiliary data for the subset we'll actually process.
        if games_to_process:
            await self._repo.prefetch_for_games(games_to_process)

        # Load historical odds snapshots once (best-effort) so we can score legs using
        # basic line movement signals without calling external APIs here.
        movement_by_game_id: Dict[str, Dict[str, Any]] = {}
        try:
            # We intentionally do not call the external API here; sport config is used to
            # ensure this sport is recognized/mapped (and for future extensions).
            _ = get_sport_config(target_sport)
            external_ids = [str(getattr(g, "external_game_id", "") or "") for g in games_to_process]
            hist_by_external = await self._odds_history_repo.get_latest_data_for_games(
                external_game_ids=external_ids,
                snapshot_kind="lookback_24h",
            )

            for g in games_to_process:
                ext = str(getattr(g, "external_game_id", "") or "")
                if not ext or ext.startswith("espn:"):
                    continue
                historical = hist_by_external.get(ext)
                if not isinstance(historical, dict):
                    continue
                current = self._odds_snapshot_builder.build(game=g, markets=getattr(g, "markets", []) or [])
                movement = self._odds_movement.build(current=current, historical=historical)
                movement_by_game_id[str(g.id)] = movement.as_dict()
        except Exception:
            # Best-effort only: do not fail parlay generation if snapshots are missing.
            movement_by_game_id = {}

        candidate_legs: List[Dict[str, Any]] = []
        processed_count = 0
        max_odds_to_process = 1000

        for game in games_to_process:
            if len(candidate_legs) >= max_legs * 2:
                break
            if processed_count >= max_odds_to_process:
                break

            for market in getattr(game, "markets", []) or []:
                if market.market_type not in ["h2h", "spreads", "totals"]:
                    continue
                if len(candidate_legs) >= max_legs * 2:
                    break
                if processed_count >= max_odds_to_process:
                    break

                for odds in getattr(market, "odds", []) or []:
                    processed_count += 1
                    if processed_count >= max_odds_to_process:
                        break

                    try:
                        leg_prob = await self._engine.calculate_leg_probability_from_odds(
                            odds,
                            market.id,
                            odds.outcome,
                            game.home_team,
                            game.away_team,
                            game.start_time,
                            market.market_type,
                        )
                    except Exception:
                        # Best-effort: a single malformed odds row should not fail the entire request.
                        continue

                    if leg_prob and leg_prob["confidence_score"] >= min_confidence:
                        move = movement_by_game_id.get(str(game.id))
                        if isinstance(move, dict):
                            leg_prob["market_move_score"] = float(
                                self._score_market_move(
                                    market_type=str(market.market_type or ""),
                                    outcome=str(odds.outcome or ""),
                                    home_team=str(game.home_team or ""),
                                    away_team=str(game.away_team or ""),
                                    movement=move,
                                )
                            )
                        leg_prob.update(
                            {
                                "game_id": str(game.id),
                                "game": f"{game.away_team} @ {game.home_team}",
                                "home_team": game.home_team,
                                "away_team": game.away_team,
                                "market_type": market.market_type,
                                "book": market.book,
                                "start_time": game.start_time.isoformat() if game.start_time else None,
                            }
                        )
                        candidate_legs.append(leg_prob)

        candidate_legs.sort(key=lambda x: x.get("confidence_score", 0), reverse=True)
        return candidate_legs[:max_legs]

    @staticmethod
    def _score_market_move(
        *,
        market_type: str,
        outcome: str,
        home_team: str,
        away_team: str,
        movement: Dict[str, Any],
    ) -> float:
        """
        Returns a small signal in [-1, 1] indicating whether market movement
        (over the snapshot window) is aligned with the selected outcome.

        This is intentionally lightweight and only used as a minor tie-breaker.
        """
        mtype = (market_type or "").lower().strip()
        outcome_str = (outcome or "").strip()

        if mtype == "h2h":
            if outcome_str.lower() == "home":
                delta = movement.get("home_implied_prob_delta")
            elif outcome_str.lower() == "away":
                delta = movement.get("away_implied_prob_delta")
            else:
                delta = None
            return _directional_score(delta, scale=0.05)

        if mtype == "spreads":
            delta_points = movement.get("spread_delta_points")
            if delta_points is None:
                return 0.0
            is_home = outcome_str.lower().startswith((home_team or "").lower().strip())
            is_away = outcome_str.lower().startswith((away_team or "").lower().strip())
            if is_home:
                # Home spread became more negative => market moved toward home.
                return _directional_score(-delta_points, scale=1.5)
            if is_away:
                return _directional_score(delta_points, scale=1.5)
            return 0.0

        if mtype == "totals":
            delta_total = movement.get("total_delta_points")
            if delta_total is None:
                return 0.0
            if outcome_str.lower().startswith("over"):
                return _directional_score(delta_total, scale=3.0)
            if outcome_str.lower().startswith("under"):
                return _directional_score(-delta_total, scale=3.0)
            return 0.0

        return 0.0

    @staticmethod
    def _resolve_date_range(target_sport: str, week: Optional[int]) -> tuple[datetime, datetime]:
        if target_sport == "NFL" and week is not None:
            week_start, week_end = get_week_date_range(week)
            return week_start, week_end

        if target_sport == "NFL":
            current_week = get_current_nfl_week()
            if current_week:
                week_start, week_end = get_week_date_range(current_week)
                return week_start, week_end

            # Before season start: fallback window.
            now = datetime.utcnow()
            return now - timedelta(hours=48), now + timedelta(days=14)

        now = datetime.utcnow()
        return now - timedelta(hours=48), now + timedelta(days=14)


def _directional_score(delta: Any, *, scale: float) -> float:
    try:
        if delta is None:
            return 0.0
        value = float(delta)
        if value == 0:
            return 0.0
        mag = min(1.0, abs(value) / float(scale))
        return (1.0 if value > 0 else -1.0) * mag
    except Exception:
        return 0.0


