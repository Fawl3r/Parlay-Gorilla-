from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from app.services.probability_engine_impl.external_data_repository import ExternalDataRepository


@dataclass(frozen=True)
class TeamStrength:
    team1_win_pct: float
    team2_win_pct: float
    team1_recent_form: float
    team2_recent_form: float
    strength_diff: float

    def to_dict(self) -> Dict[str, float]:
        return {
            "team1_win_pct": self.team1_win_pct,
            "team2_win_pct": self.team2_win_pct,
            "team1_recent_form": self.team1_recent_form,
            "team2_recent_form": self.team2_recent_form,
            "strength_diff": self.strength_diff,
        }


class TeamStrengthService:
    """Computes and caches a lightweight team-strength comparison."""

    def __init__(self, repo: ExternalDataRepository, cache: Dict[Tuple[str, str], Dict[str, float]]):
        self._repo = repo
        self._cache = cache

    async def get_team_strength(self, team1: str, team2: str) -> Optional[Dict[str, float]]:
        cache_key = (team1.lower(), team2.lower())
        if cache_key in self._cache:
            return self._cache[cache_key]

        stats1 = await self._repo.get_team_stats(team1)
        stats2 = await self._repo.get_team_stats(team2)
        if not stats1 or not stats2:
            return None

        win_pct1 = self._extract_win_pct(stats1)
        win_pct2 = self._extract_win_pct(stats2)

        form1 = await self._repo.get_recent_form(team1, games=5)
        form2 = await self._repo.get_recent_form(team2, games=5)

        recent_wins1 = self._count_recent_wins(team1, form1)
        recent_wins2 = self._count_recent_wins(team2, form2)

        # Strength difference (-1..1). Positive means team1 > team2.
        strength_diff = (win_pct1 - win_pct2) + ((recent_wins1 - recent_wins2) * 0.1)

        strength = TeamStrength(
            team1_win_pct=win_pct1,
            team2_win_pct=win_pct2,
            team1_recent_form=recent_wins1 / 5.0,
            team2_recent_form=recent_wins2 / 5.0,
            strength_diff=strength_diff,
        )

        result = strength.to_dict()
        self._cache[cache_key] = result
        return result

    @staticmethod
    def _extract_win_pct(stats: Dict[str, Any]) -> float:
        if "win_percent" in stats:
            try:
                return float(stats.get("win_percent") or 0.5)
            except Exception:
                return 0.5
        if "win_pct" in stats:
            try:
                return float(stats.get("win_pct") or 0.5)
            except Exception:
                return 0.5

        wins = float(stats.get("wins") or 0)
        losses = float(stats.get("losses") or 0)
        games = wins + losses
        return wins / games if games > 0 else 0.5

    @staticmethod
    def _count_recent_wins(team_name: str, recent_games: List[Dict[str, Any]]) -> int:
        """Count wins in recent games (best-effort across different payload shapes)."""
        wins = 0
        team_lower = (team_name or "").lower()

        for game in recent_games or []:
            if not game:
                continue

            if game.get("completed") is False:
                continue

            # Preferred shape: `is_win` boolean
            if "is_win" in game:
                if bool(game.get("is_win")):
                    wins += 1
                continue

            # Fallback shape: score comparison
            try:
                home_team = str(game.get("home_team", "")).lower()
                away_team = str(game.get("away_team", "")).lower()
                home_score = float(game.get("home_score", 0) or 0)
                away_score = float(game.get("away_score", 0) or 0)

                if team_lower and team_lower in home_team:
                    if home_score > away_score:
                        wins += 1
                elif team_lower and team_lower in away_team:
                    if away_score > home_score:
                        wins += 1
            except Exception:
                continue

        return wins


