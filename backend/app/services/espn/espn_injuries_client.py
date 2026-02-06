"""ESPN injuries client using resolved team reference (no team_abbr)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.services.data_fetchers.espn_scraper import ESPNScraper
from app.services.espn.espn_sport_resolver import EspnSportResolver
from app.services.espn.espn_team_resolver import ResolvedTeamRef

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 10.0


class EspnInjuriesClient:
    """Fetch injuries for a team using ResolvedTeamRef (team ID or injuries URL)."""

    def __init__(self, *, timeout: float = REQUEST_TIMEOUT):
        self._timeout = timeout

    async def fetch_injuries_for_team_ref(
        self,
        sport: str,
        team_ref: ResolvedTeamRef,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch injuries for the given resolved team reference.
        Returns canonical-style dict (key_players_out, injury_severity_score, total_injured, summary, unit_counts)
        or None on failure.
        """
        url = team_ref.injuries_url
        if not url and team_ref.team_id:
            base_url = EspnSportResolver.get_base_url(sport)
            url = f"{base_url}/teams/{team_ref.team_id}/injuries"
        if not url:
            logger.warning("ESPN injuries: no injuries_url or team_id for %s", team_ref.matched_name)
            return None
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url)
                if response.status_code != 200:
                    logger.warning("ESPN injuries fetch failed: %s %s", response.status_code, url)
                    return None
                data = response.json()
        except Exception as e:
            logger.warning("ESPN injuries fetch error: %s", e, extra={"url": url})
            return None
        parsed = ESPNScraper.parse_injury_response(data, sport)
        parsed.setdefault("unit_counts", {})
        return parsed
