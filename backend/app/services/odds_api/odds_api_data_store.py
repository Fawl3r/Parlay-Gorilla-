"""Persistence logic for The Odds API payloads.

Kept separate from `OddsFetcherService` to keep files small and responsibilities clear:
- `OddsFetcherService` orchestrates cache/limits/fallbacks and the high-level flow.
- `OddsApiDataStore` normalizes Odds API payloads and upserts DB rows.

Important behavior:
- Avoids duplicate `games` rows when ESPN schedule fallback has already inserted
  placeholder games (external ids like `espn:*`). We match by teams + start time
  and "promote" ESPN rows to the OddsAPI external id when safe.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import Game
from app.models.market import Market
from app.models.odds import Odds
from app.services.cache_invalidation import invalidate_after_odds_update
from app.services.sports_config import SportConfig
from app.services.team_name_normalizer import TeamNameNormalizer
from app.utils.timezone_utils import TimezoneNormalizer


class OddsApiDataStore:
    """Normalize Odds API events into `Game`/`Market`/`Odds` rows."""

    def __init__(self, db: AsyncSession):
        self._db = db
        self._team_normalizer = TeamNameNormalizer()

    async def normalize_and_store_odds(self, api_data: List[dict], sport_config: SportConfig) -> List[Game]:
        if not api_data:
            return []

        parsed_events: List[Tuple[str, str, str, datetime, dict]] = []
        for event in api_data:
            external_game_id = event.get("id")
            if not external_game_id:
                continue

            home_team = str(event.get("home_team") or "").strip()
            away_team = str(event.get("away_team") or "").strip()
            if not home_team or not away_team:
                continue

            raw_commence = event.get("commence_time", "")
            try:
                commence_time = datetime.fromisoformat(str(raw_commence).replace("Z", "+00:00"))
            except Exception:
                continue
            commence_time = TimezoneNormalizer.ensure_utc(commence_time)

            parsed_events.append((external_game_id, home_team, away_team, commence_time, event))

        if not parsed_events:
            return []

        # Batch fetch existing games by OddsAPI external ids.
        external_ids = [ext for ext, *_ in parsed_events]
        existing_games_result = await self._db.execute(
            select(Game).where(
                Game.external_game_id.in_(external_ids),
                Game.sport == sport_config.code,
            )
        )
        existing_by_external: Dict[str, Game] = {
            game.external_game_id: game for game in existing_games_result.scalars().all()
        }

        # Also fetch candidate games in the same time window to avoid duplicates with ESPN schedule rows.
        min_time = min(t for _, _, _, t, _ in parsed_events)
        max_time = max(t for _, _, _, t, _ in parsed_events)
        window_start = min_time - timedelta(hours=6)
        window_end = max_time + timedelta(hours=6)

        candidates_result = await self._db.execute(
            select(Game)
            .where(Game.sport == sport_config.code)
            .where(Game.start_time >= window_start)
            .where(Game.start_time <= window_end)
        )
        candidates = candidates_result.scalars().all()
        existing_by_match: Dict[Tuple[str, str, str], Game] = {}
        for game in candidates:
            key = self._match_key(game.home_team, game.away_team, game.start_time)
            # Prefer non-ESPN rows when we already have a clash.
            if key in existing_by_match:
                current = existing_by_match[key]
                if str(current.external_game_id).startswith("espn:") and not str(game.external_game_id).startswith("espn:"):
                    existing_by_match[key] = game
            else:
                existing_by_match[key] = game

        games: List[Game] = []

        for external_game_id, home_team, away_team, commence_time, event in parsed_events:
            game = existing_by_external.get(external_game_id)

            if game is None:
                match_key = self._match_key(home_team, away_team, commence_time)
                candidate = existing_by_match.get(match_key)
                if candidate is not None:
                    game = candidate
                    # Promote ESPN placeholder games to OddsAPI ids when safe, so future OddsAPI refreshes
                    # match by external id and we don't create duplicates.
                    if str(game.external_game_id).startswith("espn:") and external_game_id not in existing_by_external:
                        game.external_game_id = external_game_id
                    existing_by_external[external_game_id] = game
                else:
                    game = Game(
                        external_game_id=external_game_id,
                        sport=sport_config.code,
                        home_team=home_team,
                        away_team=away_team,
                        start_time=commence_time,
                        status="scheduled",
                    )
                    self._db.add(game)
                    await self._db.flush()  # get game ID
                    existing_by_external[external_game_id] = game
                    existing_by_match[self._match_key(home_team, away_team, commence_time)] = game

            # Keep core fields fresh (status may change between fetches)
            game.home_team = home_team
            game.away_team = away_team
            game.start_time = commence_time
            if getattr(game, "status", None) in (None, ""):
                game.status = "scheduled"

            # Process bookmakers (limit to first 3 books for speed)
            bookmakers = (event.get("bookmakers") or [])[:3]
            for bookmaker in bookmakers:
                book_name = str(bookmaker.get("key") or "").lower()
                markets_data = bookmaker.get("markets", []) or []

                for market_data in markets_data:
                    market_type = str(market_data.get("key") or "")
                    if market_type not in sport_config.supported_markets:
                        continue

                    outcomes = market_data.get("outcomes", []) or []

                    result = await self._db.execute(
                        select(Market)
                        .where(Market.game_id == game.id)
                        .where(Market.market_type == market_type)
                        .where(Market.book == book_name)
                        .limit(1)
                    )
                    market = result.scalar_one_or_none()

                    if not market:
                        market = Market(game_id=game.id, market_type=market_type, book=book_name)
                        self._db.add(market)
                        await self._db.flush()

                    for outcome_data in outcomes[:10]:
                        outcome_name = str(outcome_data.get("name") or "")
                        price_american = outcome_data.get("price", 0)
                        if not price_american:
                            continue

                        decimal_price = self._american_to_decimal(int(price_american))
                        implied_prob = self._decimal_to_implied_prob(decimal_price)

                        # Normalize outcome name
                        if market_type == "h2h":
                            home_norm = self._normalize_team(home_team)
                            away_norm = self._normalize_team(away_team)
                            out_norm = self._normalize_team(outcome_name)

                            if out_norm == home_norm:
                                outcome = "home"
                            elif out_norm == away_norm:
                                outcome = "away"
                            else:
                                # Soccer three-way markets include Draw/Tie.
                                lowered = outcome_name.strip().lower()
                                if lowered in ("draw", "tie", "tied"):
                                    outcome = "draw"
                                else:
                                    # Keep as-is rather than incorrectly overwriting away.
                                    outcome = lowered or "draw"
                        elif market_type == "spreads":
                            point = outcome_data.get("point", 0)
                            outcome = f"{outcome_name} {float(point):+.1f}"
                        elif market_type == "totals":
                            point = outcome_data.get("point", 0)
                            outcome = f"{outcome_name} {float(point):.1f}"
                        else:
                            outcome = outcome_name

                        result = await self._db.execute(
                            select(Odds).where(Odds.market_id == market.id).where(Odds.outcome == outcome).limit(1)
                        )
                        existing_odds = result.scalar_one_or_none()

                        formatted_price = f"+{price_american}" if int(price_american) > 0 else str(int(price_american))
                        if existing_odds:
                            existing_odds.price = formatted_price
                            existing_odds.decimal_price = decimal_price
                            existing_odds.implied_prob = implied_prob
                        else:
                            odds = Odds(
                                market_id=market.id,
                                outcome=outcome,
                                price=formatted_price,
                                decimal_price=decimal_price,
                                implied_prob=implied_prob,
                            )
                            self._db.add(odds)

            games.append(game)

        try:
            await self._db.commit()
            await invalidate_after_odds_update(self._db, sport_config.code)
        except Exception as e:
            await self._db.rollback()
            print(f"Error committing games: {e}")
            return games

        return games

    @staticmethod
    def _american_to_decimal(american_odds: int) -> Decimal:
        if american_odds > 0:
            return Decimal(american_odds) / Decimal(100) + Decimal(1)
        return Decimal(100) / Decimal(abs(american_odds)) + Decimal(1)

    @staticmethod
    def _decimal_to_implied_prob(decimal_odds: Decimal) -> Decimal:
        return Decimal(1) / decimal_odds

    def _normalize_team(self, name: str) -> str:
        return self._team_normalizer.normalize(name)

    def _match_key(self, home_team: str, away_team: str, start_time: datetime) -> Tuple[str, str, str]:
        utc = TimezoneNormalizer.ensure_utc(start_time).replace(second=0, microsecond=0)
        return (self._normalize_team(home_team), self._normalize_team(away_team), utc.isoformat())


