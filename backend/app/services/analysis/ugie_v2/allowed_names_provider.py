"""
Cache-only allowlist provider for Key Players (no roster refresh).

Returns allowed player names and per-team lists from cached apisports_team_rosters
so KeyPlayersBuilder can assign team correctly and never leak non-allowlisted names.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import Game
from app.repositories.apisports_roster_repository import ApisportsRosterRepository

# Reuse game/season/team resolution from roster context (no refresh)
from app.services.analysis.roster_context_builder import _game_team_ids_and_season


def _normalize_name(name: str) -> str:
    if not name or not isinstance(name, str):
        return ""
    return " ".join(name.split()).strip()


def _extract_ordered_names_and_positions(payload: dict) -> List[tuple[str, str]]:
    """Extract (name, position) in roster order. Position is best-effort from payload."""
    out: List[tuple[str, str]] = []
    if not isinstance(payload, dict):
        return out
    players = payload.get("players") or payload.get("response") or []
    if not isinstance(players, list):
        return out
    for p in players:
        if not isinstance(p, dict):
            continue
        name = p.get("name")
        if not name:
            first = p.get("firstname") or p.get("first_name") or ""
            last = p.get("lastname") or p.get("last_name") or ""
            name = f"{first} {last}".strip()
        if not name:
            continue
        name = _normalize_name(str(name))
        pos = (
            str(p.get("position") or p.get("pos") or p.get("role") or "").strip()
            or ""
        )
        # Nested player object (e.g. soccer squads)
        if not pos and isinstance(p.get("player"), dict):
            pos = str(
                p["player"].get("position") or p["player"].get("pos") or ""
            ).strip()
        out.append((name, pos))
    return out


@dataclass
class AllowedNamesResult:
    """Result of get_allowed_player_names_for_game (cache-only)."""

    all_names: List[str]
    by_team: Dict[str, List[str]]  # "home" -> names, "away" -> names
    positions_by_name: Dict[str, str]  # normalized name -> position (best-effort)
    updated_at: Optional[str] = None
    home_team_id: Optional[int] = None
    away_team_id: Optional[int] = None


class AllowedNamesProvider:
    """
    Provide allowed player names from cached rosters only (no refresh).
    Used by core analysis path to build key_players without quota spikes.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = ApisportsRosterRepository(db)

    async def get_allowed_player_names_for_game(
        self, game: Game
    ) -> AllowedNamesResult:
        """
        Return allowlist and per-team lists from cached rosters.
        On any failure or missing roster: empty lists / empty mapping.
        """
        empty = AllowedNamesResult(
            all_names=[],
            by_team={"home": [], "away": []},
            positions_by_name={},
            updated_at=None,
            home_team_id=None,
            away_team_id=None,
        )
        try:
            sport, team_ids, season = _game_team_ids_and_season(game)
            if not sport or not team_ids or len(team_ids) < 2:
                return empty
            rosters = await self._repo.get_rosters_for_team_ids(
                sport, team_ids, season
            )
            if not rosters:
                return empty
            home_id = team_ids[0]
            away_id = team_ids[1]
            by_team: Dict[str, List[str]] = {"home": [], "away": []}
            positions_by_name: Dict[str, str] = {}
            all_names_set: set[str] = set()
            updated_max: Optional[datetime] = None
            for row in rosters:
                tid = getattr(row, "team_id", None)
                if tid not in (home_id, away_id):
                    continue
                payload = getattr(row, "payload_json", None) or {}
                ordered = _extract_ordered_names_and_positions(payload)
                names_ordered = [n for n, _ in ordered]
                for name, pos in ordered:
                    if name:
                        all_names_set.add(name)
                        if pos:
                            positions_by_name[name] = pos
                if tid == home_id:
                    by_team["home"] = names_ordered
                elif tid == away_id:
                    by_team["away"] = names_ordered
                last_fetched = getattr(row, "last_fetched_at", None)
                if last_fetched:
                    if last_fetched.tzinfo is None:
                        last_fetched = last_fetched.replace(tzinfo=timezone.utc)
                    if updated_max is None or last_fetched > updated_max:
                        updated_max = last_fetched
            all_names = sorted(all_names_set)
            updated_at_str = (
                updated_max.isoformat() if updated_max else None
            )
            return AllowedNamesResult(
                all_names=all_names,
                by_team=by_team,
                positions_by_name=positions_by_name,
                updated_at=updated_at_str,
                home_team_id=home_id,
                away_team_id=away_id,
            )
        except Exception:
            return empty
