"""Fast core analysis generator (no long OpenAI calls).

The core payload is what the UI needs to render instantly and what search
engines need to index a text-rich page. It must be:
- deterministic and fast (seconds)
- resilient to missing stats/trends sources
- schema-compatible with the existing frontend normalizer
"""

from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.game import Game
from app.models.market import Market
from app.services.analysis.analysis_ai_writer import AnalysisAiWriter
from app.services.analysis.core_analysis_edges import CoreAnalysisEdgesBuilder
from app.services.analysis.core_analysis_picks import CorePickBuilders
from app.services.analysis.core_analysis_ui_blocks import CoreAnalysisUiBlocksBuilder
from app.services.analysis.score_projection import ScoreProjector
from app.services.model_win_probability import compute_game_win_probability
from app.services.odds_history.odds_history_provider import OddsHistoryProvider
from app.services.odds_snapshot_builder import OddsSnapshotBuilder
from app.services.stats_scraper import StatsScraperService


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

    async def generate(self, *, game: Game, timeout_seconds: float = 8.0) -> Dict[str, Any]:
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
        season = str((game.start_time or datetime.now(tz=timezone.utc)).year)
        hard_timeout = min(
            timeout_seconds,
            float(getattr(settings, "probability_prefetch_total_timeout_seconds", 12.0)),
        )
        try:
            # Clear cache before fetching to ensure fresh data
            self._stats.clear_cache()
            return await asyncio.wait_for(
                self._stats.get_matchup_data(
                    home_team=game.home_team,
                    away_team=game.away_team,
                    league=game.sport,
                    season=season,
                    game_time=game.start_time,
                ),
                timeout=hard_timeout,
            )
        except Exception as e:
            print(f"[CoreAnalysisGenerator] Error fetching matchup data: {e}")
            import traceback
            traceback.print_exc()
            return {
                "home_team_stats": None,
                "away_team_stats": None,
                "weather": None,
                "home_injuries": None,
                "away_injuries": None,
            }

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


