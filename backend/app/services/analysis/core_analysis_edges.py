"""Deterministic matchup edges for core analysis.

These are lightweight, non-AI summaries used when `full_article` isn't ready.
They help ensure all sports have meaningful "matchup" sections (NFL-like depth)
even when OpenAI is disabled.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from app.models.game import Game


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        f = float(value)
        return f
    except Exception:
        return None


def _safe_int(value: Any) -> Optional[int]:
    try:
        if value is None:
            return None
        return int(value)
    except Exception:
        return None


def _get_nested(d: Any, *keys: str) -> Any:
    current = d
    for k in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(k)
    return current


@dataclass(frozen=True)
class _TeamSnapshot:
    ppg: Optional[float]
    papg: Optional[float]
    ypg: Optional[float]
    yapg: Optional[float]
    win_pct: Optional[float]
    wins: Optional[int]
    losses: Optional[int]
    zeroed: bool


KEY_EDGES_FALLBACK_NOTE = (
    "Season split metrics incomplete — using market + last 5 games + rest context."
)


class CoreAnalysisEdgesBuilder:
    def build(
        self, *, game: Game, matchup_data: Dict[str, Any], model_probs: Dict[str, Any]
    ) -> Tuple[Dict[str, str], Dict[str, str], Optional[str], Optional[List[Dict[str, str]]]]:
        league = str(game.sport or "").upper()
        unit = self._points_unit(league)

        home_stats = matchup_data.get("home_team_stats") if isinstance(matchup_data, dict) else None
        away_stats = matchup_data.get("away_team_stats") if isinstance(matchup_data, dict) else None

        home = self._snapshot(home_stats)
        away = self._snapshot(away_stats)

        if home.zeroed or away.zeroed:
            offensive, defensive, fallback_edges = self._build_fallback_edges(
                game=game, league=league, unit=unit, model_probs=model_probs, matchup_data=matchup_data
            )
            return offensive, defensive, KEY_EDGES_FALLBACK_NOTE, fallback_edges

        offensive = self._build_offensive(game=game, league=league, unit=unit, home=home, away=away, model_probs=model_probs)
        defensive = self._build_defensive(game=game, league=league, unit=unit, home=home, away=away, model_probs=model_probs)
        return offensive, defensive, None, None

    @staticmethod
    def _points_unit(league: str) -> str:
        if league in {"MLB"}:
            return "runs"
        if league in {"NHL", "EPL", "MLS", "LALIGA", "UCL", "SOCCER"}:
            return "goals"
        return "points"

    def _snapshot(self, stats: Any) -> _TeamSnapshot:
        record = stats.get("record") if isinstance(stats, dict) else None
        offense = stats.get("offense") if isinstance(stats, dict) else None
        defense = stats.get("defense") if isinstance(stats, dict) else None

        wins = _safe_int(_get_nested(record, "wins"))
        losses = _safe_int(_get_nested(record, "losses"))
        win_pct = _safe_float(_get_nested(record, "win_percentage"))

        ppg = _safe_float(_get_nested(offense, "points_per_game"))
        ypg = _safe_float(_get_nested(offense, "yards_per_game"))
        papg = _safe_float(_get_nested(defense, "points_allowed_per_game"))
        yapg = _safe_float(_get_nested(defense, "yards_allowed_per_game"))

        # Heuristic: "zeroed" means the external stats feed likely wasn't available.
        zeroed = bool(
            (wins in (0, None))
            and (losses in (0, None))
            and (ppg in (0.0, None))
            and (papg in (0.0, None))
            and (ypg in (0.0, None))
            and (yapg in (0.0, None))
        )

        return _TeamSnapshot(
            ppg=ppg,
            papg=papg,
            ypg=ypg,
            yapg=yapg,
            win_pct=win_pct,
            wins=wins,
            losses=losses,
            zeroed=zeroed,
        )

    def _build_offensive(
        self,
        *,
        game: Game,
        league: str,
        unit: str,
        home: _TeamSnapshot,
        away: _TeamSnapshot,
        model_probs: Dict[str, Any],
    ) -> Dict[str, str]:
        home_txt = self._offense_team_edge(
            team=game.home_team,
            opponent=game.away_team,
            team_stats=home,
            opp_stats=away,
            league=league,
            unit=unit,
            perspective="home",
        )
        away_txt = self._offense_team_edge(
            team=game.away_team,
            opponent=game.home_team,
            team_stats=away,
            opp_stats=home,
            league=league,
            unit=unit,
            perspective="away",
        )

        key = self._offense_key_matchup(game=game, unit=unit, home=home, away=away, model_probs=model_probs)
        return {"home_advantage": home_txt, "away_advantage": away_txt, "key_matchup": key}

    def _build_defensive(
        self,
        *,
        game: Game,
        league: str,
        unit: str,
        home: _TeamSnapshot,
        away: _TeamSnapshot,
        model_probs: Dict[str, Any],
    ) -> Dict[str, str]:
        home_txt = self._defense_team_edge(
            team=game.home_team,
            opponent=game.away_team,
            team_stats=home,
            opp_stats=away,
            unit=unit,
        )
        away_txt = self._defense_team_edge(
            team=game.away_team,
            opponent=game.home_team,
            team_stats=away,
            opp_stats=home,
            unit=unit,
        )

        key = self._defense_key_matchup(game=game, unit=unit, home=home, away=away, model_probs=model_probs)
        return {"home_advantage": home_txt, "away_advantage": away_txt, "key_matchup": key}

    def _build_fallback_edges(
        self,
        *,
        game: Game,
        league: str,
        unit: str,
        model_probs: Dict[str, Any],
        matchup_data: Dict[str, Any],
    ) -> Tuple[Dict[str, str], Dict[str, str], List[Dict[str, str]]]:
        """When season splits are incomplete, return short edge text and consolidated fallback edges."""
        home_prob = float(model_probs.get("home_win_prob") or 0.52)
        away_prob = float(model_probs.get("away_win_prob") or 0.48)
        edges = [
            {"title": "Market-implied edge", "strength": "med", "explanation": f"Model: {game.home_team} {home_prob*100:.0f}% / {game.away_team} {away_prob*100:.0f}%."},
            {"title": "Recent form", "strength": "low", "explanation": "Using last 5 games where available."},
            {"title": "Context", "strength": "low", "explanation": "Rest and home/away factored when data present."},
        ]
        home_inj = (matchup_data or {}).get("home_injuries") or {}
        away_inj = (matchup_data or {}).get("away_injuries") or {}
        if isinstance(home_inj, dict) and isinstance(away_inj, dict) and (home_inj.get("key_players_out") or away_inj.get("key_players_out")):
            edges.append({"title": "Availability", "strength": "med", "explanation": "Key injuries reflected in impact assessment."})
        offensive = {
            "home_advantage": "Using market and recent form (see note).",
            "away_advantage": "Using market and recent form (see note).",
            "key_matchup": f"Key matchup leans on model win probability ({game.home_team} {home_prob*100:.0f}% vs {game.away_team} {away_prob*100:.0f}%).",
        }
        defensive = {
            "home_advantage": "Using market and recent form (see note).",
            "away_advantage": "Using market and recent form (see note).",
            "key_matchup": "Defensive edge uses model and context when splits are incomplete.",
        }
        return offensive, defensive, edges

    def _offense_team_edge(
        self,
        *,
        team: str,
        opponent: str,
        team_stats: _TeamSnapshot,
        opp_stats: _TeamSnapshot,
        league: str,
        unit: str,
        perspective: str,
    ) -> str:
        # Football can include yardage context when available.
        is_football = league in {"NFL", "NCAAF"}

        if team_stats.zeroed or opp_stats.zeroed:
            return "Using market and recent form (see data note)."

        ppg = team_stats.ppg
        opp_papg = opp_stats.papg
        parts = []

        if ppg is not None:
            parts.append(f"{team} is averaging {ppg:.1f} {unit} per game.")
        if opp_papg is not None:
            parts.append(f"{opponent} is allowing {opp_papg:.1f} {unit} per game.")

        if ppg is not None and opp_papg is not None:
            diff = ppg - opp_papg
            if diff > 1.0:
                parts.append("That efficiency gap suggests a favorable scoring setup for this offense.")
            elif diff < -1.0:
                parts.append("That matchup points to resistance — this offense may need explosive plays or pace to get home.")
            else:
                parts.append("On paper, this looks like a fairly even scoring matchup.")

        if is_football and team_stats.ypg and opp_stats.yapg:
            parts.append(f"Yards context: {team} at {team_stats.ypg:.1f} YPG vs {opponent} allowing {opp_stats.yapg:.1f} YPG.")

        return " ".join(parts).strip()

    def _defense_team_edge(
        self,
        *,
        team: str,
        opponent: str,
        team_stats: _TeamSnapshot,
        opp_stats: _TeamSnapshot,
        unit: str,
    ) -> str:
        if team_stats.zeroed or opp_stats.zeroed:
            return "Using market and recent form (see data note)."

        papg = team_stats.papg
        opp_ppg = opp_stats.ppg
        parts = []

        if papg is not None:
            parts.append(f"{team} is allowing {papg:.1f} {unit} per game.")
        if opp_ppg is not None:
            parts.append(f"{opponent} is scoring {opp_ppg:.1f} {unit} per game.")

        if papg is not None and opp_ppg is not None:
            diff = opp_ppg - papg
            if diff > 1.0:
                parts.append("That leans toward the opponent finding points unless this defense creates stops or turnovers.")
            elif diff < -1.0:
                parts.append("That leans toward this defense keeping the opponent in check and compressing scoring.")
            else:
                parts.append("These profiles are close enough that game flow and situational factors may decide it.")

        return " ".join(parts).strip()

    def _offense_key_matchup(
        self,
        *,
        game: Game,
        unit: str,
        home: _TeamSnapshot,
        away: _TeamSnapshot,
        model_probs: Dict[str, Any],
    ) -> str:
        if home.zeroed or away.zeroed:
            home_prob = float(model_probs.get("home_win_prob") or 0.52) * 100.0
            away_prob = float(model_probs.get("away_win_prob") or 0.48) * 100.0
            return (
                f"The key offensive question is whether the higher-probability side can turn that edge into clean scoring chances. "
                f"Our model has {game.home_team} at {home_prob:.0f}% vs {game.away_team} at {away_prob:.0f}%."
            )

        home_edge = (home.ppg - away.papg) if (home.ppg is not None and away.papg is not None) else None
        away_edge = (away.ppg - home.papg) if (away.ppg is not None and home.papg is not None) else None

        if home_edge is None and away_edge is None:
            return "Watch early pace: whichever side creates more high-quality looks (and avoids empty possessions) will control the scoring script."

        if away_edge is None or (home_edge is not None and away_edge is not None and abs(home_edge) >= abs(away_edge)):
            return (
                f"{game.home_team}'s ability to score efficiently against {game.away_team}'s defensive profile is the swing point. "
                f"If they can play above {away.papg:.1f} {unit} allowed, they’ll dictate the game script."
            )

        return (
            f"{game.away_team}'s scoring output versus {game.home_team}'s defense is the swing point. "
            f"If they can play above {home.papg:.1f} {unit} allowed, the matchup tilts their way."
        )

    def _defense_key_matchup(
        self,
        *,
        game: Game,
        unit: str,
        home: _TeamSnapshot,
        away: _TeamSnapshot,
        model_probs: Dict[str, Any],
    ) -> str:
        if home.zeroed or away.zeroed:
            return (
                "The defensive swing factor is whether either side can generate extra possessions (turnovers, second chances, or set-piece advantages) "
                "to separate in a matchup where the stat feed is still filling in."
            )

        # Favor the defense that most strongly undercuts opponent scoring.
        home_def_edge = (away.ppg - home.papg) if (away.ppg is not None and home.papg is not None) else None
        away_def_edge = (home.ppg - away.papg) if (home.ppg is not None and away.papg is not None) else None

        if home_def_edge is None and away_def_edge is None:
            return "Defensively, the team that controls tempo and forces tough looks late in possessions will have the edge."

        if away_def_edge is None or (home_def_edge is not None and away_def_edge is not None and home_def_edge >= away_def_edge):
            return (
                f"{game.home_team}'s defense versus {game.away_team}'s scoring profile is pivotal. "
                f"Holding them below {away.ppg:.1f} {unit} per game changes the math on both the spread and total."
            )

        return (
            f"{game.away_team}'s defense versus {game.home_team}'s scoring profile is pivotal. "
            f"Holding them below {home.ppg:.1f} {unit} per game changes the math on both the spread and total."
        )



