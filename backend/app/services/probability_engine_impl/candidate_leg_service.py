from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import logging

from sqlalchemy import select
from sqlalchemy import func, or_
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.event_logger import log_event
from app.models.game import Game
from app.models.market import Market
from app.services.odds_history.odds_history_snapshot_repository import OddsHistorySnapshotRepository
from app.services.odds_history.odds_movement_service import OddsMovementService
from app.services.odds_snapshot_builder import OddsSnapshotBuilder
from app.services.schedule_repair.repair_orchestrator import ScheduleRepairOrchestrator
from app.services.season_state_service import SeasonStateService
from app.services.probability_engine_impl.candidate_window_resolver import resolve_candidate_window
from app.services.probability_engine_impl.external_data_repository import ExternalDataRepository
from app.services.sports_config import get_sport_config
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
        include_player_props: bool = False,
        trace_id: Optional[str] = None,
        now_utc: Optional[datetime] = None,
    ) -> List[Dict]:
        logger = logging.getLogger(__name__)
        target_sport = (sport or getattr(self._engine, "sport_code", None) or "NFL").upper()
        now = now_utc or datetime.now(timezone.utc)
        season_svc = SeasonStateService(self._engine.db)
        season_state = await season_svc.get_season_state(target_sport, now_utc=now)
        cutoff_time, future_cutoff, mode = resolve_candidate_window(
            target_sport,
            requested_week=week,
            now_utc=now,
            season_state=season_state,
            trace_id=trace_id,
        )
        await ScheduleRepairOrchestrator(self._engine.db).repair_placeholders(
            target_sport,
            cutoff_time,
            future_cutoff,
            trace_id=trace_id,
        )
        max_games_to_process = max(1, int(settings.probability_prefetch_max_games))
        scheduled_statuses = ("scheduled", "status_scheduled")

        result = await self._engine.db.execute(
            select(Game)
            .where(Game.sport == target_sport)
            .where(Game.start_time >= cutoff_time)
            .where(Game.start_time <= future_cutoff)
            .where(or_(Game.status.is_(None), func.lower(Game.status).in_(scheduled_statuses)))
            .order_by(Game.start_time)
            .limit(max_games_to_process)
            .options(selectinload(Game.markets).selectinload(Market.odds))
        )
        games_to_process = result.scalars().all()
        games_with_markets = sum(1 for g in games_to_process if getattr(g, "markets", None))
        total_markets = sum(len(getattr(g, "markets", []) or []) for g in games_to_process)
        total_odds = sum(
            len(getattr(m, "odds", []) or [])
            for g in games_to_process
            for m in (getattr(g, "markets", []) or [])
        )
        log_event(
            logger,
            "parlay.generate.games_queried",
            trace_id=trace_id,
            sport=target_sport,
            games_count=len(games_to_process),
            window_start=cutoff_time.isoformat(),
            window_end=future_cutoff.isoformat(),
        )
        log_event(
            logger,
            "parlay.generate.market_coverage",
            trace_id=trace_id,
            sport=target_sport,
            games_with_markets=games_with_markets,
            total_markets=total_markets,
            total_odds=total_odds,
        )
        if not games_to_process and mode == "week":
            cutoff_time, future_cutoff, _ = resolve_candidate_window(
                target_sport,
                requested_week=None,
                now_utc=now,
                season_state=season_state,
                trace_id=trace_id,
            )
            result = await self._engine.db.execute(
                select(Game)
                .where(Game.sport == target_sport)
                .where(Game.start_time >= cutoff_time)
                .where(Game.start_time <= future_cutoff)
                .where(or_(Game.status.is_(None), func.lower(Game.status).in_(scheduled_statuses)))
                .order_by(Game.start_time)
                .limit(max_games_to_process)
                .options(selectinload(Game.markets).selectinload(Market.odds))
            )
            games_to_process = result.scalars().all()
            games_with_markets = sum(1 for g in games_to_process if getattr(g, "markets", None))
            total_markets = sum(len(getattr(g, "markets", []) or []) for g in games_to_process)
            total_odds = sum(
                len(getattr(m, "odds", []) or [])
                for g in games_to_process
                for m in (getattr(g, "markets", []) or [])
            )
        
        if not games_to_process:
            # Try a wider date range as fallback if no games found in initial range
            now = datetime.now(timezone.utc)
            wider_cutoff = now - timedelta(days=7)  # Look back 1 week
            wider_future = now + timedelta(days=30)  # Look forward 1 month
            
            logger.info(
                f"No games found in initial range {cutoff_time} to {future_cutoff}, "
                f"trying wider range: {wider_cutoff} to {wider_future}"
            )
            
            wider_result = await self._engine.db.execute(
                select(Game)
                .where(Game.sport == target_sport)
                .where(Game.start_time >= wider_cutoff)
                .where(Game.start_time <= wider_future)
                .where(or_(Game.status.is_(None), func.lower(Game.status).in_(scheduled_statuses)))
                .order_by(Game.start_time)
                .limit(max_games_to_process)
                .options(selectinload(Game.markets).selectinload(Market.odds))
            )
            games_to_process = wider_result.scalars().all()
            
            if games_to_process:
                logger.info(f"Found {len(games_to_process)} games in wider date range")
                # Update the cutoff/future times for logging consistency
                cutoff_time = wider_cutoff
                future_cutoff = wider_future
            else:
                # Check if there are any games at all for this sport (even without date filters)
                total_games_result = await self._engine.db.execute(
                    select(Game)
                    .where(Game.sport == target_sport)
                    .where(or_(Game.status.is_(None), func.lower(Game.status).in_(scheduled_statuses)))
                    .limit(10)
                )
                total_games = total_games_result.scalars().all()
                logger.warning(
                    f"No games found for {target_sport} in date range {cutoff_time} to {future_cutoff} "
                    f"(week={week}). Total scheduled games for {target_sport}: {len(total_games)}"
                )

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
        
        # Log processing start
        logger.info(
            f"Processing {len(games_to_process)} games to build candidate legs "
            f"(max_legs={max_legs}, min_confidence={min_confidence})"
        )

        for game in games_to_process:
            if len(candidate_legs) >= max_legs * 2:
                break
            if processed_count >= max_odds_to_process:
                break

            for market in getattr(game, "markets", []) or []:
                allowed_markets = ["h2h", "spreads", "totals"]
                if include_player_props:
                    allowed_markets.append("player_props")
                if market.market_type not in allowed_markets:
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

        # Log final candidate leg count before filtering
        logger.info(
            f"Built {len(candidate_legs)} candidate legs from {processed_count} odds processed. "
            f"Filtering to top {max_legs} by confidence score."
        )

        candidate_legs.sort(key=lambda x: x.get("confidence_score", 0), reverse=True)
        final_legs = candidate_legs[:max_legs]
        
        # Log final result
        if final_legs:
            avg_confidence = sum(leg.get("confidence_score", 0) for leg in final_legs) / len(final_legs)
            logger.info(
                f"Returning {len(final_legs)} candidate legs (avg confidence: {avg_confidence:.1f})"
            )
        else:
            logger.warning(
                f"No candidate legs returned after processing {len(games_to_process)} games. "
                f"This may indicate: no markets/odds loaded, all odds below min_confidence={min_confidence}, "
                f"or processing errors."
            )
        
        return final_legs

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
        """Resolve date range for candidate leg queries.
        
        For NFL: Always use full week range (Thursday-Monday games)
        For other sports: Use multi-day window to capture games across multiple days
        """
        logger = logging.getLogger(__name__)
        now = datetime.now(timezone.utc)
        
        if target_sport == "NFL" and week is not None:
            try:
                week_start, week_end = get_week_date_range(week)
                logger.info(
                    f"Date range for NFL Week {week}: {week_start.isoformat()} to {week_end.isoformat()} "
                    f"(span: {(week_end - week_start).total_seconds() / 86400:.1f} days)"
                )
                return week_start, week_end
            except Exception as e:
                logger.warning(f"Failed to get date range for NFL Week {week}: {e}, using fallback")
                # Fallback to current week or extended window
                current_week = get_current_nfl_week()
                if current_week:
                    week_start, week_end = get_week_date_range(current_week)
                    logger.info(f"Using current week {current_week} as fallback: {week_start.isoformat()} to {week_end.isoformat()}")
                    return week_start, week_end

        if target_sport == "NFL":
            current_week = get_current_nfl_week()
            if current_week:
                week_start, week_end = get_week_date_range(current_week)
                logger.info(
                    f"Date range for NFL (current week {current_week}): {week_start.isoformat()} to {week_end.isoformat()} "
                    f"(span: {(week_end - week_start).total_seconds() / 86400:.1f} days)"
                )
                return week_start, week_end

            # Before season start or off-season: use extended window to capture upcoming games
            logger.info(
                f"NFL off-season detected (no current week), using extended window: "
                f"{(now - timedelta(days=3)).isoformat()} to {(now + timedelta(days=14)).isoformat()}"
            )
            # Look back 3 days (to catch games that might have started), forward 14 days (2 weeks)
            # This gives us a much larger window to find games during off-season
            return now - timedelta(days=3), now + timedelta(days=14)

        # For other sports (NBA, NHL, MLB, etc.): use multi-day window
        # These sports have games spread across multiple days of the week
        # NBA: Games typically Mon-Sun, with heavy slates on Wed/Fri/Sat
        # NHL: Games throughout the week, often Tue/Thu/Sat
        # MLB: Games almost daily during season
        cutoff = now - timedelta(days=1)
        future = now + timedelta(days=7)
        logger.info(
            f"Date range for {target_sport}: {cutoff.isoformat()} to {future.isoformat()} "
            f"(span: {(future - cutoff).total_seconds() / 86400:.1f} days)"
        )
        # Look back ~1 day and forward ~7 days to capture multi-day slates without
        # scanning too far ahead (keeps candidate generation fast and relevant).
        return cutoff, future


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


