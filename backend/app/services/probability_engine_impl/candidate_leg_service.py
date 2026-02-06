from __future__ import annotations

import heapq
import logging
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.event_logger import log_event
from app.repositories.odds_repository import fetch_minimal_odds_rows
from app.services.odds_history.odds_history_snapshot_repository import OddsHistorySnapshotRepository
from app.services.odds_history.odds_movement_service import OddsMovementService
from app.services.odds_snapshot_builder import OddsSnapshotBuilder
from app.services.schedule_repair.repair_orchestrator import ScheduleRepairOrchestrator
from app.services.season_state_service import SeasonStateService
from app.services.probability_engine_impl.candidate_leg_cache import (
    build_candidate_legs_cache_key,
    get_candidate_leg_cache,
)
from app.services.probability_engine_impl.candidate_leg_query import fetch_minimal_game_rows
from app.services.probability_engine_impl.candidate_window_resolver import resolve_candidate_window
from app.services.probability_engine_impl.external_data_repository import ExternalDataRepository
from app.services.sports_config import get_sport_config
from app.utils.memory import log_mem
from app.utils.nfl_week import get_week_date_range, get_current_nfl_week


def _odds_like(row: dict) -> Any:
    """Build an odds-like object for calculate_leg_probability_from_odds."""
    return SimpleNamespace(
        implied_prob=row.get("implied_prob", 0.0),
        decimal_price=row.get("decimal_price", 1.0),
        price=row.get("price", ""),
        outcome=row.get("outcome", ""),
    )


def _build_snapshot_from_rows(
    builder: OddsSnapshotBuilder,
    game_dict: dict,
    rows_for_game: List[dict],
) -> Dict[str, Any]:
    """Build snapshot dict from minimal odds rows for one game (for movement scoring)."""
    by_type: Dict[str, List[dict]] = {}
    for r in rows_for_game:
        mtype = (r.get("market_type") or "").lower()
        if mtype not in by_type:
            by_type[mtype] = []
        by_type[mtype].append(r)
    markets = []
    for mtype, rows in by_type.items():
        if not rows:
            continue
        odds_list = [SimpleNamespace(outcome=r["outcome"], implied_prob=r["implied_prob"], price=r["price"], created_at=r.get("created_at")) for r in rows]
        markets.append(SimpleNamespace(market_type=mtype, book=rows[0].get("book", ""), odds=odds_list))
    game_obj = SimpleNamespace(home_team=game_dict.get("home_team"), away_team=game_dict.get("away_team"))
    return builder.build(game=game_obj, markets=markets)


class CandidateLegService:
    """Builds candidate legs for parlay generation using minimal queries (no ORM graph load)."""

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
        max_games_cap = max(1, int(getattr(settings, "parlay_max_games_considered", 20)))
        max_games_to_process = min(
            max(1, int(settings.probability_prefetch_max_games)),
            max_games_cap,
        )
        max_legs_cap = max(1, int(getattr(settings, "parlay_max_legs_considered", 150)))
        max_markets_per_game = max(1, int(getattr(settings, "parlay_max_markets_per_game", 2)))
        max_props_per_game = max(0, int(getattr(settings, "parlay_max_props_per_game", 2)))
        max_odds_to_process = max(1, int(getattr(settings, "parlay_max_odds_rows_processed", 600)))
        scheduled_statuses = ("scheduled", "status_scheduled")
        cache_ttl = max(1, int(getattr(settings, "candidate_legs_cache_ttl_seconds", 45)))

        cache = get_candidate_leg_cache()
        cache_key = build_candidate_legs_cache_key(
            sport=target_sport,
            date_utc=now.date().isoformat(),
            week=week,
            include_player_props=include_player_props,
        )
        cached_list = await cache.get(cache_key)
        if cached_list is not None:
            n_return = min(max_legs, len(cached_list), max_legs_cap)
            final_legs = (
                heapq.nlargest(n_return, cached_list, key=lambda x: x.get("confidence_score", 0))
                if cached_list
                else []
            )
            logger.info(
                "parlay.generate.candidates cache_hit sport=%s key=%s cached_count=%s returned=%s",
                target_sport,
                cache_key,
                len(cached_list),
                len(final_legs),
            )
            return final_legs

        log_mem(logger, "candidate_legs_before_game_query", {"sport": target_sport, "trace_id": trace_id})

        games_to_process = await fetch_minimal_game_rows(
            self._engine.db,
            sport=target_sport,
            cutoff_time=cutoff_time,
            future_cutoff=future_cutoff,
            scheduled_statuses=scheduled_statuses,
            limit=max_games_to_process,
        )
        if not games_to_process and mode == "week":
            cutoff_time, future_cutoff, _ = resolve_candidate_window(
                target_sport,
                requested_week=None,
                now_utc=now,
                season_state=season_state,
                trace_id=trace_id,
            )
            games_to_process = await fetch_minimal_game_rows(
                self._engine.db,
                sport=target_sport,
                cutoff_time=cutoff_time,
                future_cutoff=future_cutoff,
                scheduled_statuses=scheduled_statuses,
                limit=max_games_to_process,
            )
        if not games_to_process:
            wider_cutoff = now - timedelta(days=7)
            wider_future = now + timedelta(days=30)
            logger.info(
                "No games in initial range, trying wider %s to %s",
                wider_cutoff.isoformat(),
                wider_future.isoformat(),
            )
            games_to_process = await fetch_minimal_game_rows(
                self._engine.db,
                sport=target_sport,
                cutoff_time=wider_cutoff,
                future_cutoff=wider_future,
                scheduled_statuses=scheduled_statuses,
                limit=max_games_to_process,
            )
            if games_to_process:
                cutoff_time, future_cutoff = wider_cutoff, wider_future

        log_mem(logger, "candidate_legs_after_game_query", {"games": len(games_to_process), "trace_id": trace_id})

        game_ids = [g["id"] for g in games_to_process]
        allowed_markets = ["h2h", "spreads", "totals"]
        if include_player_props:
            allowed_markets.append("player_props")
        odds_rows = await fetch_minimal_odds_rows(
            self._engine.db,
            game_ids=game_ids,
            allowed_market_keys=allowed_markets,
            max_rows=max_odds_to_process,
        )
        log_mem(logger, "candidate_legs_after_odds_fetch", {"odds_rows": len(odds_rows), "trace_id": trace_id})
        total_odds = len(odds_rows)
        games_with_markets = sum(1 for g in games_to_process if any(r["game_id"] == g["id"] for r in odds_rows))
        total_markets = len(set((r["game_id"], r["market_id"]) for r in odds_rows))

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
        if games_to_process and total_odds == 0:
            logger.warning(
                "No candidate legs: games_total=%s but total_odds=0. Skipping prefetch.",
                len(games_to_process),
            )
            return []

        by_game: Dict[Any, List[dict]] = {}
        for r in odds_rows:
            by_game.setdefault(r["game_id"], []).append(r)

        game_like_for_prefetch = [SimpleNamespace(home_team=g["home_team"], away_team=g["away_team"], start_time=g["start_time"]) for g in games_to_process]
        await self._repo.prefetch_for_games(game_like_for_prefetch)

        movement_by_game_id: Dict[str, Dict[str, Any]] = {}
        try:
            _ = get_sport_config(target_sport)
            external_ids = [str(g.get("external_game_id") or "") for g in games_to_process]
            hist_by_external = await self._odds_history_repo.get_latest_data_for_games(
                external_game_ids=external_ids,
                snapshot_kind="lookback_24h",
            )
            for g in games_to_process:
                ext = str(g.get("external_game_id") or "")
                if not ext or ext.startswith("espn:"):
                    continue
                historical = hist_by_external.get(ext)
                if not isinstance(historical, dict):
                    continue
                rows_for_game = by_game.get(g["id"], [])
                if not rows_for_game:
                    continue
                current = _build_snapshot_from_rows(self._odds_snapshot_builder, g, rows_for_game)
                movement = self._odds_movement.build(current=current, historical=historical)
                movement_by_game_id[str(g["id"])] = movement.as_dict()
        except Exception:
            movement_by_game_id = {}

        candidate_legs: List[Dict[str, Any]] = []
        processed_count = 0
        truncated_by_cap = False
        games_total = len(games_to_process)
        games_with_odds = 0
        games_with_h2h = 0
        games_with_spreads = 0
        games_with_totals = 0
        legs_rejected_below_confidence = 0
        legs_rejected_bad_lines = 0

        logger.info(
            "Processing %s games to build candidate legs (max_legs=%s, min_confidence=%s, max_legs_cap=%s)",
            games_total,
            max_legs,
            min_confidence,
            max_legs_cap,
        )

        for game in games_to_process:
            if len(candidate_legs) >= max_legs_cap:
                truncated_by_cap = True
                break
            if processed_count >= max_odds_to_process:
                break
            game_rows = by_game.get(game["id"], [])
            main_markets_used = 0
            props_used = 0
            seen_market_types: set[str] = set()
            game_has_odds = False
            game_has_h2h = False
            game_has_spreads = False
            game_has_totals = False

            for row in game_rows:
                if len(candidate_legs) >= max_legs_cap or processed_count >= max_odds_to_process:
                    if len(candidate_legs) >= max_legs_cap:
                        truncated_by_cap = True
                    break
                mtype = str(row.get("market_type") or "")
                if mtype not in allowed_markets:
                    continue
                if mtype not in seen_market_types:
                    seen_market_types.add(mtype)
                    if mtype == "player_props":
                        props_used += 1
                    else:
                        main_markets_used += 1
                if mtype == "player_props":
                    if props_used > max_props_per_game:
                        continue
                else:
                    if main_markets_used > max_markets_per_game:
                        continue
                processed_count += 1
                if mtype == "h2h":
                    game_has_h2h = True
                elif mtype == "spreads":
                    game_has_spreads = True
                elif mtype == "totals":
                    game_has_totals = True
                game_has_odds = True

                odds_like = _odds_like(row)
                start_time = game.get("start_time")
                try:
                    leg_prob = await self._engine.calculate_leg_probability_from_odds(
                        odds_like,
                        row["market_id"],
                        row["outcome"],
                        game.get("home_team") or "",
                        game.get("away_team") or "",
                        start_time,
                        mtype,
                    )
                except Exception:
                    legs_rejected_bad_lines += 1
                    continue
                if not leg_prob or leg_prob.get("confidence_score", 0) < min_confidence:
                    if leg_prob is None:
                        continue
                    legs_rejected_below_confidence += 1
                    continue
                move = movement_by_game_id.get(str(game["id"]))
                if isinstance(move, dict):
                    leg_prob["market_move_score"] = float(
                        self._score_market_move(
                            market_type=mtype,
                            outcome=str(row.get("outcome") or ""),
                            home_team=str(game.get("home_team") or ""),
                            away_team=str(game.get("away_team") or ""),
                            movement=move,
                        )
                    )
                leg_prob.update({
                    "game_id": str(game["id"]),
                    "game": f"{game.get('away_team')} @ {game.get('home_team')}",
                    "home_team": game.get("home_team"),
                    "away_team": game.get("away_team"),
                    "market_type": mtype,
                    "book": row.get("book"),
                    "start_time": start_time.isoformat() if hasattr(start_time, "isoformat") else str(start_time) if start_time else None,
                })
                candidate_legs.append(leg_prob)

            if game_has_odds:
                games_with_odds += 1
            if game_has_h2h:
                games_with_h2h += 1
            if game_has_spreads:
                games_with_spreads += 1
            if game_has_totals:
                games_with_totals += 1

        log_mem(logger, "candidate_legs_after_build", {"candidate_count": len(candidate_legs), "trace_id": trace_id})
        if truncated_by_cap or len(candidate_legs) > max_legs_cap:
            log_event(
                logger,
                "parlay.candidates_truncated",
                trace_id=trace_id,
                sport=target_sport,
                candidate_count=len(candidate_legs),
                max_legs_cap=max_legs_cap,
            )
        n_return = min(max_legs, len(candidate_legs), max_legs_cap)
        final_legs = (
            heapq.nlargest(n_return, candidate_legs, key=lambda x: x.get("confidence_score", 0))
            if candidate_legs
            else []
        )

        logger.info(
            "parlay.generate.candidates built games_total=%s games_with_odds=%s games_with_h2h=%s "
            "games_with_spreads=%s games_with_totals=%s candidate_legs=%s selected_legs=%s "
            "odds_processed=%s legs_rejected_below_confidence=%s legs_rejected_bad_lines=%s",
            games_total,
            games_with_odds,
            games_with_h2h,
            games_with_spreads,
            games_with_totals,
            len(candidate_legs),
            len(final_legs),
            processed_count,
            legs_rejected_below_confidence,
            legs_rejected_bad_lines,
        )
        if not final_legs:
            logger.warning(
                "No candidate legs returned after processing %s games (min_confidence=%s); "
                "games_with_odds=%s h2h=%s spreads=%s totals=%s rejected_below=%s rejected_bad=%s",
                games_total,
                min_confidence,
                games_with_odds,
                games_with_h2h,
                games_with_spreads,
                games_with_totals,
                legs_rejected_below_confidence,
                legs_rejected_bad_lines,
            )
        elif final_legs:
            avg_conf = sum(leg.get("confidence_score", 0) for leg in final_legs) / len(final_legs)
            logger.info("Returning %s candidate legs (avg confidence %.1f)", len(final_legs), avg_conf)

        try:
            await cache.set(cache_key, candidate_legs, ttl_seconds=cache_ttl)
        except Exception as set_err:
            logger.debug("Candidate legs cache set failed: %s", set_err)

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
        now = datetime.now(timezone.utc)
        if target_sport == "NFL" and week is not None:
            try:
                return get_week_date_range(week)
            except Exception:
                current_week = get_current_nfl_week()
                if current_week:
                    return get_week_date_range(current_week)
                return now - timedelta(days=3), now + timedelta(days=14)
        if target_sport == "NFL":
            current_week = get_current_nfl_week()
            if current_week:
                return get_week_date_range(current_week)
            return now - timedelta(days=3), now + timedelta(days=14)
        return now - timedelta(days=1), now + timedelta(days=7)


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
