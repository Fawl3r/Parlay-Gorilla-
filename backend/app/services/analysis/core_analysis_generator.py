"""Fast core analysis generator (no long OpenAI calls).

The core payload is what the UI needs to render instantly and what search
engines need to index a text-rich page. It must be:
- deterministic and fast (seconds)
- resilient to missing stats/trends sources
- schema-compatible with the existing frontend normalizer
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.game import Game
from app.models.market import Market
from app.models.game_analysis import GameAnalysis

logger = logging.getLogger(__name__)
from app.services.analysis.analysis_ai_writer import AnalysisAiWriter
from app.services.analysis.builders.confidence_breakdown_builder import ConfidenceBreakdownBuilder
from app.services.analysis.builders.market_disagreement_builder import MarketDisagreementBuilder
from app.services.analysis.builders.outcome_paths_builder import OutcomePathsBuilder
from app.services.analysis.builders.portfolio_guidance_builder import PortfolioGuidanceBuilder
from app.services.analysis.builders.prop_recommendations_builder import PropRecommendationsBuilder
from app.services.analysis.builders.delta_summary_builder import DeltaSummaryBuilder
from app.services.analysis.builders.seo_structured_data_builder import SEOStructuredDataBuilder
from app.services.traffic_ranker import TrafficRanker
from app.services.fetch_budget import FetchBudgetManager
from app.services.analysis.core_analysis_edges import CoreAnalysisEdgesBuilder
from app.services.analysis.core_analysis_picks import CorePickBuilders
from app.services.analysis.core_analysis_ui_blocks import CoreAnalysisUiBlocksBuilder
from app.services.analysis.score_projection import ScoreProjector
from app.services.model_win_probability import compute_game_win_probability
from app.services.odds_history.odds_history_provider import OddsHistoryProvider
from app.services.odds_snapshot_builder import OddsSnapshotBuilder
from app.services.stats_scraper import StatsScraperService
from app.services.stats.fallback_manager import FetchContext


class CoreAnalysisGenerator:
    def __init__(
        self,
        db: AsyncSession,
        *,
        stats_scraper: Optional[StatsScraperService] = None,
        ai_writer: Optional[AnalysisAiWriter] = None,
    ):
        self._db = db
        self._stats = stats_scraper or StatsScraperService(db)
        self._ai_writer = ai_writer or AnalysisAiWriter()
        self._odds_snapshot_builder = OddsSnapshotBuilder()
        self._odds_history = OddsHistoryProvider(db)
        self._picks = CorePickBuilders()
        self._edges = CoreAnalysisEdgesBuilder()
        # Request-scoped cache to prevent duplicate fetches within same generation
        self._request_cache: Dict[str, Any] = {}

    async def generate(self, *, game: Game, timeout_seconds: float = 8.0) -> Dict[str, Any]:
        start_time = time.time()
        external_calls_count = 0
        cache_hit = False
        
        markets = await self._load_markets(game_id=game.id)
        odds_snapshot = self._odds_snapshot_builder.build(game=game, markets=markets)
        line_movement = await self._odds_history.get_line_movement(game=game, current_snapshot=odds_snapshot)

        matchup_data = await self._safe_matchup_data(game=game, timeout_seconds=timeout_seconds)
        model = await compute_game_win_probability(
            db=self._db,
            home_team=game.home_team,
            away_team=game.away_team,
            sport=game.sport,
            matchup_data=matchup_data,
            odds_data=odds_snapshot,
        )

        home_prob = float(model.get("home_model_prob", 0.52))
        away_prob = float(model.get("away_model_prob", 0.48))
        projection = ScoreProjector.project(league=game.sport, home_prob=home_prob, away_prob=away_prob)

        model_probs = {
            "home_win_prob": home_prob,
            "away_win_prob": away_prob,
            "ai_confidence": float(model.get("ai_confidence", 30.0)),
            "calculation_method": str(model.get("calculation_method", "unknown")),
            "score_projection": projection.as_str(),
            "explanation": (
                "This is the AI’s estimate of how often each team would win this matchup."
            ),
        }

        ats_trends, totals_trends = self._build_trends(matchup_data=matchup_data, game=game)
        spread_pick = self._picks.build_spread_pick(game=game, odds_snapshot=odds_snapshot, model_probs=model_probs, projection=projection)
        total_pick = self._picks.build_total_pick(game=game, odds_snapshot=odds_snapshot, model_probs=model_probs, projection=projection)
        offensive_edges, defensive_edges = self._edges.build(game=game, matchup_data=matchup_data, model_probs=model_probs)

        draft: Dict[str, Any] = {
            "headline": f"{game.away_team} vs {game.home_team} — Quick Take and picks",
            "subheadline": f"{game.away_team} @ {game.home_team} — who the AI favors, how sure it is, and the best action.",
            "opening_summary": self._build_opening_summary(
                game=game,
                odds_snapshot=odds_snapshot,
                model_probs=model_probs,
                line_movement=line_movement,
            ),
            "offensive_matchup_edges": offensive_edges,
            "defensive_matchup_edges": defensive_edges,
            "key_stats": self._build_key_stats(
                game=game,
                odds_snapshot=odds_snapshot,
                model_probs=model_probs,
                line_movement=line_movement,
            ),
            "ats_trends": ats_trends,
            "totals_trends": totals_trends,
            "market_movement": line_movement or {},
            "weather_considerations": self._build_weather_considerations(matchup_data=matchup_data),
            "model_win_probability": model_probs,
            "ai_spread_pick": spread_pick,
            "ai_total_pick": total_pick,
            "best_bets": self._picks.build_best_bets(game=game, spread_pick=spread_pick, total_pick=total_pick, model_probs=model_probs),
            "same_game_parlays": self._picks.build_same_game_parlays(game=game, spread_pick=spread_pick, total_pick=total_pick),
            "full_article": "",  # generated in background
        }
        
        # Add new FREE-mode builders
        try:
            # Market Disagreement
            market_disagreement = MarketDisagreementBuilder.build(
                odds_snapshot=odds_snapshot,
                model_probs=model_probs,
                markets=markets,
            )
            draft["market_disagreement"] = market_disagreement
            
            # Outcome Paths
            spread_point = odds_snapshot.get("home_spread_point")
            total_line = odds_snapshot.get("total_line")
            outcome_paths = OutcomePathsBuilder.build(
                odds_snapshot=odds_snapshot,
                model_probs=model_probs,
                spread=spread_point,
                total=total_line,
            )
            draft["outcome_paths"] = outcome_paths
            
            # Confidence Breakdown
            market_probs = {
                "home_implied_prob": odds_snapshot.get("home_implied_prob"),
                "away_implied_prob": odds_snapshot.get("away_implied_prob"),
            }
            confidence_breakdown = ConfidenceBreakdownBuilder.build(
                market_probs=market_probs,
                model_probs=model_probs,
                matchup_data=matchup_data,
                odds_snapshot=odds_snapshot,
            )
            draft["confidence_breakdown"] = confidence_breakdown
            
            # Portfolio Guidance
            portfolio_guidance = PortfolioGuidanceBuilder.build(
                spread_pick=spread_pick,
                total_pick=total_pick,
                same_game_parlays=draft.get("same_game_parlays", {}),
                confidence_total=confidence_breakdown.get("confidence_total", 0.0),
            )
            draft["portfolio_guidance"] = portfolio_guidance
            
            # Props recommendations (traffic-gated and fetch-budget-gated)
            try:
                traffic_ranker = TrafficRanker(self._db)
                fetch_budget = FetchBudgetManager(self._db)
                
                # Check traffic gate first
                props_enabled = await traffic_ranker.is_props_enabled_for_game(
                    game_id=game.id,
                    league=game.sport,
                )
                
                if props_enabled:
                    # Check fetch budget
                    props_key = f"props:{game.id}"
                    if await fetch_budget.should_fetch(props_key, ttl_seconds=21600):  # 6 hours
                        # Build props snapshot
                        props_snapshot = self._odds_snapshot_builder.build_props_snapshot(
                            game=game,
                            markets=markets,
                        )
                        
                        if props_snapshot.get("props"):
                            prop_recommendations = PropRecommendationsBuilder.build(
                                props_snapshot=props_snapshot,
                                game=game,
                            )
                            if prop_recommendations:
                                draft["prop_recommendations"] = prop_recommendations
                                await fetch_budget.mark_fetched(props_key, ttl_seconds=21600)
            except Exception as props_error:
                # Never fail core generation due to props errors
                print(f"[CoreAnalysisGenerator] Error generating props: {props_error}")
        except Exception as e:
            # Never fail core generation due to builder errors
            print(f"[CoreAnalysisGenerator] Error in FREE-mode builders: {e}")
            import traceback
            traceback.print_exc()

        # Ensure confidence_breakdown is always set so core readiness and UI meter work for all sports.
        cb = draft.get("confidence_breakdown")
        if not isinstance(cb, dict) or "confidence_total" not in cb:
            draft["confidence_breakdown"] = {
                "market_agreement": 0.0,
                "statistical_edge": 0.0,
                "situational_edge": 0.0,
                "data_quality": 0.0,
                "confidence_total": 0.0,
                "explanation": "Confidence breakdown could not be calculated.",
                "trend": None,
            }

        # Build delta summary (What Changed)
        previous_analysis = None
        try:
            result = await self._db.execute(
                select(GameAnalysis)
                .where(GameAnalysis.game_id == game.id)
                .where(GameAnalysis.league == game.sport)
                .order_by(GameAnalysis.version.desc())
                .limit(1)
            )
            prev_record = result.scalar_one_or_none()
            if prev_record and prev_record.analysis_content:
                previous_analysis = prev_record.analysis_content
        except Exception:
            pass  # Ignore errors fetching previous analysis
        
        delta_summary = DeltaSummaryBuilder.build(
            current_analysis=draft,
            previous_analysis=previous_analysis,
            line_movement=line_movement,
            matchup_data=matchup_data,
        )
        draft["delta_summary"] = delta_summary
        
        # Build SEO structured data (JSON-LD)
        seo_structured_data = SEOStructuredDataBuilder.build(
            game=game,
            analysis=draft,
            odds_snapshot=odds_snapshot,
        )
        draft["seo_structured_data"] = seo_structured_data
        
        # Add generation metadata with staleness indicators
        core_ms = int((time.time() - start_time) * 1000)
        now = datetime.now(tz=timezone.utc)
        
        # Calculate data freshness (age in hours)
        odds_age_hours = 0.0
        if odds_snapshot.get("last_updated"):
            try:
                odds_updated = datetime.fromisoformat(odds_snapshot["last_updated"].replace("Z", "+00:00"))
                odds_age_hours = (now - odds_updated).total_seconds() / 3600
            except (ValueError, AttributeError):
                pass
        
        stats_age_hours = 0.0
        if matchup_data.get("stats_fetched_at"):
            try:
                stats_fetched = datetime.fromisoformat(matchup_data["stats_fetched_at"].replace("Z", "+00:00"))
                stats_age_hours = (now - stats_fetched).total_seconds() / 3600
            except (ValueError, AttributeError):
                pass
        
        injuries_age_hours = 0.0
        if matchup_data.get("injuries_fetched_at"):
            try:
                injuries_fetched = datetime.fromisoformat(matchup_data["injuries_fetched_at"].replace("Z", "+00:00"))
                injuries_age_hours = (now - injuries_fetched).total_seconds() / 3600
            except (ValueError, AttributeError):
                pass
        
        # Extract data quality if available (from v2 platform)
        home_data_quality = matchup_data.get("home_data_quality")
        away_data_quality = matchup_data.get("away_data_quality")
        
        draft["generation"] = {
            "run_mode": "FREE",
            "data_sources_used": {
                "odds": bool(odds_snapshot.get("home_ml")),
                "stats": bool(matchup_data.get("home_team_stats")),
                "injuries": bool(matchup_data.get("home_injuries")),
                "weather": bool(matchup_data.get("weather")),
                "form": bool(matchup_data.get("home_team_stats", {}).get("recent_form")),
            },
            "metrics": {
                "core_ms": core_ms,
                "external_calls_count": external_calls_count,
                "cache_hit": cache_hit,
            },
            "data_freshness": {
                "odds_age_hours": round(odds_age_hours, 2),
                "stats_age_hours": round(stats_age_hours, 2),
                "injuries_age_hours": round(injuries_age_hours, 2),
            },
        }
        
        # Add data quality if available
        if home_data_quality or away_data_quality:
            draft["generation"]["data_quality"] = {
                "home": home_data_quality,
                "away": away_data_quality,
            }
            # Add warnings to data_sources_used
            if home_data_quality:
                draft["generation"]["data_sources_used"]["home_trust_score"] = home_data_quality.get("trust_score", 0.0)
                draft["generation"]["data_sources_used"]["home_warnings"] = home_data_quality.get("warnings", [])
            if away_data_quality:
                draft["generation"]["data_sources_used"]["away_trust_score"] = away_data_quality.get("trust_score", 0.0)
                draft["generation"]["data_sources_used"]["away_warnings"] = away_data_quality.get("warnings", [])

        # Add decision-first UI blocks for the redesigned analysis page.
        try:
            ui_blocks = CoreAnalysisUiBlocksBuilder.for_sport(game.sport).build(
                home_team=game.home_team,
                away_team=game.away_team,
                model_probs=model_probs,
                opening_summary=draft.get("opening_summary") or "",
                spread_pick=spread_pick or {},
                total_pick=total_pick or {},
                offensive_edges=offensive_edges or {},
                defensive_edges=defensive_edges or {},
                ats_trends=ats_trends or {},
                totals_trends=totals_trends or {},
                weather_considerations=draft.get("weather_considerations") or "",
            )
            draft.update(ui_blocks)
        except Exception:
            # Never fail core generation due to UI block generation.
            pass

        # UGIE v2: attach structured intelligence payload (never fail generation).
        try:
            from app.services.analysis.roster_context_builder import RosterContextBuilder
            from app.services.analysis.ugie_v2.ugie_v2_builder import (
                UgieV2Builder,
                get_minimal_ugie_v2,
            )
            from app.services.analysis.ugie_v2.allowed_names_provider import AllowedNamesProvider
            from app.services.analysis.ugie_v2.validation import (
                validate_and_clamp_ugie_v2,
                ugie_compact_summary,
            )
            from app.services.analysis.weather.weather_impact_engine import WeatherImpactEngine
            from app.core.event_logger import log_event
            import logging
            _ugie_log = logging.getLogger(__name__)
            roster_ctx = RosterContextBuilder(self._db)
            try:
                await roster_ctx.ensure_rosters_for_game(game)
            except Exception:
                _ugie_log.info("UGIE roster warm failed; continuing cache-only", exc_info=True)
            weather_block = WeatherImpactEngine.compute(
                game.sport or "", matchup_data.get("weather")
            )
            allowed_result = await AllowedNamesProvider(self._db).get_allowed_player_names_for_game(game)
            redaction_count = None
            if isinstance(draft.get("generation"), dict):
                redaction_count = draft["generation"].get("redaction_count")
            draft["ugie_v2"] = UgieV2Builder.build(
                draft=draft,
                matchup_data=matchup_data,
                game=game,
                odds_snapshot=odds_snapshot,
                model_probs=model_probs,
                weather_block=weather_block,
                allowed_player_names=allowed_result.all_names,
                allowlist_by_team=allowed_result.by_team,
                positions_by_name=allowed_result.positions_by_name,
                redaction_count=redaction_count,
                updated_at=allowed_result.updated_at,
            )
            validate_and_clamp_ugie_v2(draft["ugie_v2"])
            summary = ugie_compact_summary(draft["ugie_v2"])
            log_event(
                _ugie_log,
                "ugie_v2_built",
                level=logging.INFO,
                game_id=game.id,
                sport=game.sport,
                **summary,
            )
            if _ugie_log.isEnabledFor(logging.DEBUG):
                import json
                _trimmed = json.dumps(draft["ugie_v2"], default=str, separators=(",", ":"))[:4000]
                log_event(_ugie_log, "ugie_v2_full", level=logging.DEBUG, game_id=game.id, ugie_json=_trimmed)
        except Exception:
            from app.services.analysis.ugie_v2.ugie_v2_builder import get_minimal_ugie_v2
            draft["ugie_v2"] = get_minimal_ugie_v2()

        # Best-effort polish (strict timeout, never required).
        return await self._ai_writer.polish_core_copy(
            matchup=f"{game.away_team} @ {game.home_team}",
            league=game.sport,
            model_probs=model_probs,
            odds_snapshot=odds_snapshot,
            draft=draft,
            timeout_seconds=float(getattr(settings, "analysis_core_ai_polish_timeout_seconds", 4.0)),
        )

    async def _load_markets(self, *, game_id) -> List[Market]:
        result = await self._db.execute(
            select(Market).where(Market.game_id == game_id).options(selectinload(Market.odds))
        )
        return result.scalars().all()

    async def _safe_matchup_data(self, *, game: Game, timeout_seconds: float) -> Dict[str, Any]:
        # Check request-scoped cache first
        cache_key = f"matchup:{game.id}"
        if cache_key in self._request_cache:
            return self._request_cache[cache_key]
        
        season = str((game.start_time or datetime.now(tz=timezone.utc)).year)
        hard_timeout = min(
            timeout_seconds,
            float(getattr(settings, "probability_prefetch_total_timeout_seconds", 12.0)),
        )
        try:
            # Check if we should use stats platform v2 (feature flag)
            use_v2 = getattr(settings, "use_stats_platform_v2", False)
            
            if use_v2:
                # Use new stats platform v2
                from app.services.fetch_budget import FetchBudgetManager
                from app.services.sports.sport_registry import get_season_mode
                
                # Determine traffic gate
                traffic_ranker = TrafficRanker(self._db)
                traffic_gate = await traffic_ranker.is_props_enabled_for_game(game.id, game.sport)
                
                # Create fetch context
                fetch_budget = FetchBudgetManager(self._db)
                context = FetchContext(
                    game_time=game.start_time,
                    traffic_gate=traffic_gate,
                    fetch_budget=fetch_budget,
                    season_mode=get_season_mode(game.sport, datetime.now(tz=timezone.utc)),
                )
                
                # Get bundles for both teams
                home_bundle_task = self._stats.get_team_bundle(
                    game.home_team, game.sport, season, context
                )
                away_bundle_task = self._stats.get_team_bundle(
                    game.away_team, game.sport, season, context
                )
                
                # Get weather separately (not part of bundle)
                # Weather fetching is complex (needs city/state), so use legacy method for now
                weather = None
                if game.sport in ["NFL", "MLB"]:
                    try:
                        # Weather is fetched in get_matchup_data, so we'll get it from there
                        # For now, fetch weather separately using the existing method
                        from app.services.data_fetchers.weather import WeatherFetcher
                        weather_fetcher = WeatherFetcher()
                        weather_data = await weather_fetcher.get_game_weather(
                            home_team=game.home_team,
                            game_time=game.start_time,
                        )
                        if weather_data:
                            weather = {
                                "temperature": weather_data.get("temperature", 0),
                                "feels_like": weather_data.get("feels_like", 0),
                                "description": weather_data.get("description", weather_data.get("condition", "clear")),
                                "wind_speed": weather_data.get("wind_speed", 0),
                                "wind_direction": weather_data.get("wind_direction", 0),
                                "humidity": weather_data.get("humidity", 0),
                                "precipitation": weather_data.get("precipitation", 0),
                                "condition": weather_data.get("condition", "clear"),
                                "is_outdoor": weather_data.get("is_outdoor", True),
                                "affects_game": weather_data.get("affects_game", False),
                            }
                            # Add impact assessment
                            if hasattr(self._stats, '_assess_weather_impact_from_data'):
                                weather["impact_assessment"] = self._stats._assess_weather_impact_from_data(weather_data)
                    except Exception as e:
                        print(f"[CoreAnalysisGenerator] Error fetching weather: {e}")
                        weather = None
                
                # Gather bundle tasks
                results = await asyncio.wait_for(
                    asyncio.gather(home_bundle_task, away_bundle_task, return_exceptions=True),
                    timeout=hard_timeout,
                )
                
                home_bundle = results[0] if not isinstance(results[0], Exception) else {}
                away_bundle = results[1] if not isinstance(results[1], Exception) else {}
                
                # Convert bundles to matchup_data format (backward compatibility)
                matchup_data = {
                    "home_team_stats": home_bundle.get("canonical_stats"),
                    "away_team_stats": away_bundle.get("canonical_stats"),
                    "home_injuries": home_bundle.get("injury_json"),
                    "away_injuries": away_bundle.get("injury_json"),
                    "weather": weather,
                    "head_to_head": None,
                    # New v2 fields
                    "home_features": home_bundle.get("derived_features"),
                    "away_features": away_bundle.get("derived_features"),
                    "home_data_quality": home_bundle.get("data_quality"),
                    "away_data_quality": away_bundle.get("data_quality"),
                    "home_source_flags": home_bundle.get("source_flags", []),
                    "away_source_flags": away_bundle.get("source_flags", []),
                }
                
                # Add fetch timestamps
                now = datetime.now(tz=timezone.utc)
                matchup_data["stats_fetched_at"] = now.isoformat()
                matchup_data["injuries_fetched_at"] = now.isoformat()
                if weather:
                    matchup_data["weather"]["fetched_at"] = now.isoformat()
            else:
                # Use legacy get_matchup_data
                self._stats.clear_cache()
                matchup_data = await asyncio.wait_for(
                    self._stats.get_matchup_data(
                        home_team=game.home_team,
                        away_team=game.away_team,
                        league=game.sport,
                        season=season,
                        game_time=game.start_time,
                    ),
                    timeout=hard_timeout,
                )
                # Add fetch timestamps for staleness tracking
                now = datetime.now(tz=timezone.utc)
                matchup_data["stats_fetched_at"] = now.isoformat()
                matchup_data["injuries_fetched_at"] = now.isoformat()
                if matchup_data.get("weather"):
                    matchup_data["weather"]["fetched_at"] = now.isoformat()
            
            # Cache in request scope
            self._request_cache[cache_key] = matchup_data
            return matchup_data
        except Exception as e:
            print(f"[CoreAnalysisGenerator] Error fetching matchup data: {e}")
            import traceback
            traceback.print_exc()
            fallback = {
                "home_team_stats": None,
                "away_team_stats": None,
                "weather": None,
                "home_injuries": None,
                "away_injuries": None,
            }
            self._request_cache[cache_key] = fallback
            return fallback

    def _build_trends(self, *, matchup_data: Dict[str, Any], game: Game) -> Tuple[Dict[str, str], Dict[str, str]]:
        home_stats = matchup_data.get("home_team_stats") if isinstance(matchup_data, dict) else None
        away_stats = matchup_data.get("away_team_stats") if isinstance(matchup_data, dict) else None

        home_ats = (home_stats or {}).get("ats_trends") if isinstance(home_stats, dict) else {}
        away_ats = (away_stats or {}).get("ats_trends") if isinstance(away_stats, dict) else {}
        home_ou = (home_stats or {}).get("over_under_trends") if isinstance(home_stats, dict) else {}
        away_ou = (away_stats or {}).get("over_under_trends") if isinstance(away_stats, dict) else {}

        ats = {
            "home_team_trend": self._format_ats(team=game.home_team, ats=home_ats or {}),
            "away_team_trend": self._format_ats(team=game.away_team, ats=away_ats or {}),
            "analysis": self._compare_ats(home=home_ats or {}, away=away_ats or {}, home_team=game.home_team, away_team=game.away_team),
        }
        totals = {
            "home_team_trend": self._format_ou(team=game.home_team, ou=home_ou or {}),
            "away_team_trend": self._format_ou(team=game.away_team, ou=away_ou or {}),
            "analysis": self._compare_ou(home=home_ou or {}, away=away_ou or {}, home_team=game.home_team, away_team=game.away_team),
        }
        return ats, totals

    @staticmethod
    def _format_ats(*, team: str, ats: Dict[str, Any]) -> str:
        wins = int(ats.get("wins") or 0)
        losses = int(ats.get("losses") or 0)
        pushes = int(ats.get("pushes") or 0)
        games = wins + losses + pushes
        if games <= 0:
            return f"ATS data is not currently available for {team}."
        # Database stores percentages as 0-100, so if > 1.0, it's already a percentage
        raw_pct = float(ats.get("win_percentage") or 0.0)
        # Clamp to 0-100 range to prevent display errors (e.g., 10000%)
        if raw_pct > 100.0:
            # If somehow > 100, it was likely already multiplied incorrectly - clamp to 100
            pct = 100.0
        elif raw_pct > 1.0:
            # Already in 0-100 format
            pct = raw_pct
        else:
            # In 0-1 format, convert to 0-100
            pct = raw_pct * 100.0
        # Final clamp to ensure never exceeds 100%
        pct = min(100.0, max(0.0, pct))
        recent = str(ats.get("recent") or "").strip()
        recent_clause = f" Recent: {recent} ATS." if recent else ""
        return f"{team} is {wins}-{losses}-{pushes} ATS ({pct:.1f}% cover rate).{recent_clause}"

    @staticmethod
    def _format_ou(*, team: str, ou: Dict[str, Any]) -> str:
        overs = int(ou.get("overs") or 0)
        unders = int(ou.get("unders") or 0)
        games = overs + unders
        if games <= 0:
            return f"Over/under data is not currently available for {team}."
        # Database stores percentages as 0-100, so if > 1.0, it's already a percentage
        raw_pct = float(ou.get("over_percentage") or 0.0)
        # Clamp to 0-100 range to prevent display errors (e.g., 10000%)
        if raw_pct > 100.0:
            # If somehow > 100, it was likely already multiplied incorrectly - clamp to 100
            pct = 100.0
        elif raw_pct > 1.0:
            # Already in 0-100 format
            pct = raw_pct
        else:
            # In 0-1 format, convert to 0-100
            pct = raw_pct * 100.0
        # Final clamp to ensure never exceeds 100%
        pct = min(100.0, max(0.0, pct))
        avg = ou.get("avg_total_points")
        avg_clause = f" Avg total: {float(avg):.1f}." if avg else ""
        return f"{team} totals have gone Over {overs} times and Under {unders} times ({pct:.1f}% over rate).{avg_clause}"

    @staticmethod
    def _compare_ats(*, home: Dict[str, Any], away: Dict[str, Any], home_team: str, away_team: str) -> str:
        home_games = int(home.get("wins") or 0) + int(home.get("losses") or 0) + int(home.get("pushes") or 0)
        away_games = int(away.get("wins") or 0) + int(away.get("losses") or 0) + int(away.get("pushes") or 0)
        if home_games <= 0 or away_games <= 0:
            logger.debug(
                "ATS limited: home_team=%s home_games=%s away_team=%s away_games=%s",
                home_team, home_games, away_team, away_games,
            )
            return "ATS trend data is limited for this matchup. We're leaning more on the model and current prices."
        # Database stores percentages as 0-100, so if > 1.0, it's already a percentage
        raw_home_pct = float(home.get("win_percentage") or 0.0)
        raw_away_pct = float(away.get("win_percentage") or 0.0)
        # Clamp to 0-100 range to prevent display errors
        home_pct = min(100.0, max(0.0, raw_home_pct if raw_home_pct > 1.0 else raw_home_pct * 100.0))
        away_pct = min(100.0, max(0.0, raw_away_pct if raw_away_pct > 1.0 else raw_away_pct * 100.0))
        leader = home_team if home_pct >= away_pct else away_team
        return f"{leader} has been the more reliable ATS side so far ({home_team} {home_pct:.1f}% vs {away_team} {away_pct:.1f}%)."

    @staticmethod
    def _compare_ou(*, home: Dict[str, Any], away: Dict[str, Any], home_team: str, away_team: str) -> str:
        home_games = int(home.get("overs") or 0) + int(home.get("unders") or 0)
        away_games = int(away.get("overs") or 0) + int(away.get("unders") or 0)
        if home_games <= 0 or away_games <= 0:
            return "Totals trend data is limited for this matchup. We're leaning more on pace, efficiency, and the posted number."
        # Database stores percentages as 0-100, so if > 1.0, it's already a percentage
        raw_home_pct = float(home.get("over_percentage") or 0.0)
        raw_away_pct = float(away.get("over_percentage") or 0.0)
        # Clamp to 0-100 range to prevent display errors
        home_pct = min(100.0, max(0.0, raw_home_pct if raw_home_pct > 1.0 else raw_home_pct * 100.0))
        away_pct = min(100.0, max(0.0, raw_away_pct if raw_away_pct > 1.0 else raw_away_pct * 100.0))
        leaning = "Over" if (home_pct + away_pct) / 2.0 >= 50.0 else "Under"
        return f"Combined O/U tendencies point slightly toward the {leaning} (home {home_pct:.1f}% over, away {away_pct:.1f}% over)."

    @staticmethod
    def _build_opening_summary(
        *,
        game: Game,
        odds_snapshot: Dict[str, Any],
        model_probs: Dict[str, Any],
        line_movement: Optional[Dict[str, Any]] = None,
    ) -> str:
        home_prob = float(model_probs.get("home_win_prob") or 0.52) * 100.0
        away_prob = float(model_probs.get("away_win_prob") or 0.48) * 100.0
        total_line = odds_snapshot.get("total_line")
        home_spread = odds_snapshot.get("home_spread_point")

        line_bits: List[str] = []
        if home_spread is not None:
            try:
                line_bits.append(f"spread: {game.home_team} {float(home_spread):+.1f}")
            except Exception:
                pass
        if total_line is not None:
            try:
                line_bits.append(f"total: {float(total_line):.1f}")
            except Exception:
                pass
        lines_clause = f" Market snapshot ({', '.join(line_bits)})." if line_bits else ""
        movement_clause = ""
        if isinstance(line_movement, dict):
            movement_summary = str(line_movement.get("summary") or "").strip()
            if movement_summary:
                movement_clause = f" {movement_summary}"

        return (
            f"{game.away_team} visits {game.home_team} with betting interest on both sides of the number.{lines_clause}{movement_clause} "
            f"Our model makes {game.home_team} the slight favorite ({home_prob:.0f}% vs {away_prob:.0f}%). "
            "Below are our spread/total leans plus the top best-bet angles based on the current market."
        )

    @staticmethod
    def _build_key_stats(
        *,
        game: Game,
        odds_snapshot: Dict[str, Any],
        model_probs: Dict[str, Any],
        line_movement: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        home_prob = float(model_probs.get("home_win_prob") or 0.52) * 100.0
        away_prob = float(model_probs.get("away_win_prob") or 0.48) * 100.0
        bits = [
            f"Model win probability: {game.home_team} {home_prob:.0f}% vs {game.away_team} {away_prob:.0f}%.",
            f"Projected score: {model_probs.get('score_projection', 'TBD')}.",
        ]
        if odds_snapshot.get("home_spread_point") is not None:
            bits.append(f"Spread: {game.home_team} {float(odds_snapshot['home_spread_point']):+.1f}.")
        if odds_snapshot.get("total_line") is not None:
            bits.append(f"Total: {float(odds_snapshot['total_line']):.1f}.")
        if isinstance(line_movement, dict):
            movement_summary = str(line_movement.get("summary") or "").strip()
            if movement_summary:
                bits.append(movement_summary)
        return bits

    @staticmethod
    def _build_weather_considerations(*, matchup_data: Dict[str, Any]) -> str:
        weather = matchup_data.get("weather") if isinstance(matchup_data, dict) else None
        if not isinstance(weather, dict):
            return ""
        if not weather.get("is_outdoor", True):
            return "This game will be played indoors/dome conditions, so weather should not affect gameplay."
        if not weather.get("affects_game", False):
            return ""
        temp = weather.get("temperature")
        wind = weather.get("wind_speed")
        desc = weather.get("description") or weather.get("condition")
        bits: List[str] = []
        if desc:
            bits.append(str(desc))
        if temp is not None:
            bits.append(f"{temp}°F")
        if wind is not None:
            bits.append(f"wind {wind} mph")
        extra = f" ({', '.join(bits)})" if bits else ""
        return f"Weather may influence game flow{extra}."


