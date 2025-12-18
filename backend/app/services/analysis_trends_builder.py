"""
Deterministic trend copy builder for analysis pages.

We use AI for long-form analysis, but ATS / O-U cards should always reflect the
best available data in our database to avoid stale "not available" copy when we
do have partial season results.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from app.models.team_stats import TeamStats


@dataclass(frozen=True)
class _AtsSnapshot:
    wins: int
    losses: int
    pushes: int
    win_pct: float  # 0-100
    recent: Tuple[int, int]
    home: Tuple[int, int]
    away: Tuple[int, int]

    @property
    def decided(self) -> int:
        return self.wins + self.losses


@dataclass(frozen=True)
class _OuSnapshot:
    overs: int
    unders: int
    over_pct: float  # 0-100
    recent: Tuple[int, int]
    avg_total_points: float

    @property
    def total(self) -> int:
        return self.overs + self.unders


class AnalysisTrendsBuilder:
    """Build ATS and totals trend text from TeamStats rows."""

    def build_ats_trends(
        self,
        home_team: str,
        away_team: str,
        home_stats: Optional[TeamStats],
        away_stats: Optional[TeamStats],
    ) -> Dict[str, str]:
        home = self._get_ats(home_stats)
        away = self._get_ats(away_stats)

        return {
            "home_team_trend": self._format_ats_team_trend(home_team, home),
            "away_team_trend": self._format_ats_team_trend(away_team, away),
            "analysis": self._format_ats_matchup_analysis(home_team, away_team, home, away),
        }

    def build_totals_trends(
        self,
        home_team: str,
        away_team: str,
        home_stats: Optional[TeamStats],
        away_stats: Optional[TeamStats],
    ) -> Dict[str, str]:
        home = self._get_ou(home_stats)
        away = self._get_ou(away_stats)

        return {
            "home_team_trend": self._format_ou_team_trend(home_team, home),
            "away_team_trend": self._format_ou_team_trend(away_team, away),
            "analysis": self._format_ou_matchup_analysis(home_team, away_team, home, away),
        }

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------
    @staticmethod
    def _safe_int(value: Any) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _safe_float(value: Any) -> float:
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    def _get_ats(self, stats: Optional[TeamStats]) -> Optional[_AtsSnapshot]:
        if not stats:
            return None

        wins = self._safe_int(getattr(stats, "ats_wins", 0))
        losses = self._safe_int(getattr(stats, "ats_losses", 0))
        pushes = self._safe_int(getattr(stats, "ats_pushes", 0))
        decided = wins + losses

        win_pct = self._safe_float(getattr(stats, "ats_win_percentage", 0.0))
        if decided > 0 and win_pct <= 0.0:
            win_pct = (wins / decided) * 100.0

        recent_w = self._safe_int(getattr(stats, "ats_recent_wins", 0))
        recent_l = self._safe_int(getattr(stats, "ats_recent_losses", 0))
        home_w = self._safe_int(getattr(stats, "ats_home_wins", 0))
        home_l = self._safe_int(getattr(stats, "ats_home_losses", 0))
        away_w = self._safe_int(getattr(stats, "ats_away_wins", 0))
        away_l = self._safe_int(getattr(stats, "ats_away_losses", 0))

        return _AtsSnapshot(
            wins=wins,
            losses=losses,
            pushes=pushes,
            win_pct=win_pct,
            recent=(recent_w, recent_l),
            home=(home_w, home_l),
            away=(away_w, away_l),
        )

    def _get_ou(self, stats: Optional[TeamStats]) -> Optional[_OuSnapshot]:
        if not stats:
            return None

        overs = self._safe_int(getattr(stats, "over_wins", 0))
        unders = self._safe_int(getattr(stats, "under_wins", 0))
        total = overs + unders

        over_pct = self._safe_float(getattr(stats, "over_percentage", 0.0))
        if total > 0 and over_pct <= 0.0:
            over_pct = (overs / total) * 100.0

        recent_over = self._safe_int(getattr(stats, "over_recent_count", 0))
        recent_under = self._safe_int(getattr(stats, "under_recent_count", 0))
        avg_total_points = self._safe_float(getattr(stats, "avg_total_points", 0.0))

        return _OuSnapshot(
            overs=overs,
            unders=unders,
            over_pct=over_pct,
            recent=(recent_over, recent_under),
            avg_total_points=avg_total_points,
        )

    def _format_ats_team_trend(self, team: str, ats: Optional[_AtsSnapshot]) -> str:
        if not ats or ats.decided <= 0:
            return f"ATS data is not currently available for {team}."

        record = f"{ats.wins}-{ats.losses}"
        if ats.pushes > 0:
            record = f"{ats.wins}-{ats.losses}-{ats.pushes}"

        sample_note = " (small sample)" if ats.decided < 4 else ""
        parts = [f"{team} is {record} ATS this season ({ats.win_pct:.1f}% cover rate){sample_note}."]

        rw, rl = ats.recent
        if (rw + rl) > 0:
            parts.append(f"Over their last 5 games, they are {rw}-{rl} ATS.")

        hw, hl = ats.home
        if (hw + hl) > 0:
            parts.append(f"At home: {hw}-{hl} ATS.")

        aw, al = ats.away
        if (aw + al) > 0:
            parts.append(f"On the road: {aw}-{al} ATS.")

        return " ".join(parts).strip()

    def _format_ou_team_trend(self, team: str, ou: Optional[_OuSnapshot]) -> str:
        if not ou or ou.total <= 0:
            return f"Over/under data is not currently available for {team}."

        sample_note = " (small sample)" if ou.total < 4 else ""
        parts = [f"{team}'s games are {ou.overs}-{ou.unders} to the over this season ({ou.over_pct:.1f}% over rate){sample_note}."]

        ro, ru = ou.recent
        if (ro + ru) > 0:
            parts.append(f"In their last 5, they've gone over {ro}-{ru}.")

        if ou.avg_total_points > 0:
            parts.append(f"Their games average {ou.avg_total_points:.1f} total points.")

        return " ".join(parts).strip()

    def _format_ats_matchup_analysis(
        self,
        home_team: str,
        away_team: str,
        home: Optional[_AtsSnapshot],
        away: Optional[_AtsSnapshot],
    ) -> str:
        home_has = bool(home and home.decided > 0)
        away_has = bool(away and away.decided > 0)

        if home_has and away_has:
            return (
                f"{home_team} is {home.wins}-{home.losses} ATS ({home.win_pct:.1f}%), "
                f"while {away_team} is {away.wins}-{away.losses} ATS ({away.win_pct:.1f}%). "
                "Use those cover rates as context, but prioritize matchup edges and line value."
            )
        if home_has and not away_has:
            return (
                f"{home_team} has started {home.wins}-{home.losses} ATS ({home.win_pct:.1f}%), "
                f"but {away_team} ATS results are not available yet. "
                "This is a spot where the spread pick should lean more on matchup and market context than trends."
            )
        if away_has and not home_has:
            return (
                f"{away_team} has started {away.wins}-{away.losses} ATS ({away.win_pct:.1f}%), "
                f"but {home_team} ATS results are not available yet. "
                "This is a spot where the spread pick should lean more on matchup and market context than trends."
            )
        return "ATS trend data is not currently available for this matchup yet."

    def _format_ou_matchup_analysis(
        self,
        home_team: str,
        away_team: str,
        home: Optional[_OuSnapshot],
        away: Optional[_OuSnapshot],
    ) -> str:
        home_has = bool(home and home.total > 0)
        away_has = bool(away and away.total > 0)

        if home_has and away_has:
            return (
                f"{home_team} is {home.overs}-{home.unders} to the over ({home.over_pct:.1f}%), "
                f"and {away_team} is {away.overs}-{away.unders} ({away.over_pct:.1f}%). "
                "Pair those rates with pace, efficiency, and matchup factors when evaluating the total."
            )
        if home_has and not away_has:
            return (
                f"{home_team} is {home.overs}-{home.unders} to the over ({home.over_pct:.1f}%), "
                f"but {away_team} totals results are not available yet. "
                "Lean on matchup/tempo indicators more than trend data when sizing the total bet."
            )
        if away_has and not home_has:
            return (
                f"{away_team} is {away.overs}-{away.unders} to the over ({away.over_pct:.1f}%), "
                f"but {home_team} totals results are not available yet. "
                "Lean on matchup/tempo indicators more than trend data when sizing the total bet."
            )
        return "Over/under trend data is not currently available for this matchup yet."





