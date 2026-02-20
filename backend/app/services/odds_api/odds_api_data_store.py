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
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import Game
from app.models.market import Market
from app.models.odds import Odds
from app.services.cache_invalidation import invalidate_after_odds_update
from app.services.game_match_key import (
    CanonicalGameMatchKey,
    build_canonical_key,
    canonical_key_to_string,
)
from app.services.game_status_normalizer import GameStatusNormalizer
from app.services.season_phase_helper import infer_season_phase_from_text
from app.services.sports_config import SportConfig
from app.services.team_name_normalizer import TeamNameNormalizer
from app.utils.timezone_utils import TimezoneNormalizer
from app.utils.nfl_week import calculate_nfl_week


# Bookmakers allowed for player props (premium feature)
PLAYER_PROPS_BOOKS = ["fanduel", "draftkings"]


def _event_season_phase(event: dict) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Infer season_phase, stage, round from Odds API event. Never from date."""
    phase: Optional[str] = None
    stage: Optional[str] = None
    round_val: Optional[str] = None
    if event.get("is_playoff") or event.get("is_postseason"):
        phase = "postseason"
        stage = str(event.get("description") or event.get("group") or "").strip() or None
        return (phase, stage, round_val)
    for key in ("description", "group", "sport_title"):
        raw = event.get(key)
        if not raw:
            continue
        text = str(raw).strip()
        inferred = infer_season_phase_from_text(text)
        if inferred:
            phase = inferred
            stage = text or None
            return (phase, stage, round_val)
    return (phase, stage, round_val)


class OddsApiDataStore:
    """Normalize Odds API events into `Game`/`Market`/`Odds` rows."""

    def __init__(self, db: AsyncSession):
        self._db = db
        self._team_normalizer = TeamNameNormalizer()

    async def normalize_and_store_odds(
        self, api_data: List[dict], sport_config: SportConfig, _retry: bool = False
    ) -> List[Game]:
        if not api_data:
            return []

        parsed_events: List[Tuple[str, str, str, datetime, dict]] = []
        for event in api_data:
            external_game_id = event.get("id")
            if not external_game_id:
                continue

            home_team = str(event.get("home_team") or "").strip()
            away_team = str(event.get("away_team") or "").strip()
            
            # Filter out games with empty team names
            if not home_team or not away_team:
                continue
            
            # List of placeholder team names
            placeholder_names = {
                "TBD", "TBA", "TBC",  # To Be Determined/Announced/Confirmed
                "AFC", "NFC",  # Conference placeholders (NFL post-season)
                "TO BE DETERMINED", "TO BE ANNOUNCED",
                "TBD TEAM", "TBA TEAM",
            }
            
            home_upper = home_team.upper()
            away_upper = away_team.upper()
            
            # If we have placeholder team names, try to extract actual team names from market outcomes
            if home_upper in placeholder_names or away_upper in placeholder_names:
                import logging
                logger = logging.getLogger(__name__)
                
                # Try to extract actual team names from market outcomes (h2h, spreads, totals)
                bookmakers = event.get("bookmakers", [])
                extracted_home = None
                extracted_away = None
                all_outcome_names = []
                
                # Check all bookmakers and all market types
                for bookmaker in bookmakers:
                    markets = bookmaker.get("markets", [])
                    for market in markets:
                        market_key = market.get("key", "")
                        outcomes = market.get("outcomes", [])
                        
                        for outcome in outcomes:
                            outcome_name = str(outcome.get("name", "")).strip()
                            if outcome_name and outcome_name.upper() not in placeholder_names:
                                all_outcome_names.append(outcome_name)
                        
                        # For h2h markets, try to identify home/away
                        if market_key == "h2h" and len(outcomes) >= 2:
                            outcome_names = [str(outcome.get("name", "")).strip() for outcome in outcomes[:2]]
                            valid_outcomes = [name for name in outcome_names if name.upper() not in placeholder_names]
                            
                            if len(valid_outcomes) >= 2:
                                # h2h: typically [away, home] order
                                extracted_away = valid_outcomes[0]
                                extracted_home = valid_outcomes[1]
                                logger.info(
                                    f"Extracted from h2h: {extracted_away} @ {extracted_home} "
                                    f"(external_id: {external_game_id})"
                                )
                                break
                    
                    if extracted_home and extracted_away:
                        break
                
                # If h2h didn't work, try spreads (they often have team names)
                if not extracted_home or not extracted_away:
                    for bookmaker in bookmakers:
                        markets = bookmaker.get("markets", [])
                        for market in markets:
                            if market.get("key") == "spreads":
                                outcomes = market.get("outcomes", [])
                                spread_teams = []
                                for outcome in outcomes:
                                    outcome_name = str(outcome.get("name", "")).strip()
                                    if outcome_name and outcome_name.upper() not in placeholder_names:
                                        spread_teams.append(outcome_name)
                                
                                if len(spread_teams) >= 2:
                                    extracted_away = spread_teams[0]
                                    extracted_home = spread_teams[1]
                                    logger.info(
                                        f"Extracted from spreads: {extracted_away} @ {extracted_home} "
                                        f"(external_id: {external_game_id})"
                                    )
                                    break
                        
                        if extracted_home and extracted_away:
                            break
                
                # If still no valid names, use unique outcome names we found
                if not extracted_home or not extracted_away:
                    unique_names = list(dict.fromkeys(all_outcome_names))  # Preserve order, remove duplicates
                    if len(unique_names) >= 2:
                        extracted_away = unique_names[0]
                        extracted_home = unique_names[1]
                        logger.info(
                            f"Extracted from all outcomes: {extracted_away} @ {extracted_home} "
                            f"(external_id: {external_game_id})"
                        )
                
                if extracted_home and extracted_away and extracted_home.upper() not in placeholder_names and extracted_away.upper() not in placeholder_names:
                    # Use extracted team names from outcomes
                    home_team = extracted_home
                    away_team = extracted_away
                    logger.info(
                        f"✅ Successfully extracted actual team names: {away_team} @ {home_team} "
                        f"(external_id: {external_game_id}, sport: {sport_config.code})"
                    )
                else:
                    # Could not extract valid team names - will need ESPN fallback or skip
                    raw_commence = event.get("commence_time", "")
                    try:
                        commence_time = datetime.fromisoformat(str(raw_commence).replace("Z", "+00:00"))
                        commence_time = TimezoneNormalizer.ensure_utc(commence_time)
                    except Exception:
                        commence_time = None
                    
                    is_postseason = False
                    if sport_config.code == "NFL" and commence_time:
                        try:
                            week = calculate_nfl_week(commence_time)
                            is_postseason = week is not None and week >= 19
                        except Exception:
                            pass
                    
                    logger.warning(
                        f"❌ Could not extract valid team names from API response. "
                        f"Event has: {away_team} @ {home_team} "
                        f"(external_id: {external_game_id}, sport: {sport_config.code}, "
                        f"postseason: {is_postseason}, found {len(all_outcome_names)} outcome names: {all_outcome_names[:4]})"
                    )
                    # Don't skip - let it through and rely on ESPN fallback in odds_fetcher
                    # This way existing games can be updated

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
        existing_by_match: Dict[CanonicalGameMatchKey, Game] = {}
        for game in candidates:
            key = build_canonical_key(
                sport_config.code,
                game.home_team,
                game.away_team,
                game.start_time,
                team_normalizer=self._team_normalizer,
                sport_for_normalizer=sport_config.code,
            )
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
                match_key = build_canonical_key(
                    sport_config.code,
                    home_team,
                    away_team,
                    commence_time,
                    team_normalizer=self._team_normalizer,
                    sport_for_normalizer=sport_config.code,
                )
                candidate = existing_by_match.get(match_key)
                if candidate is not None:
                    game = candidate
                    # Promote ESPN placeholder games to OddsAPI ids when safe, so future OddsAPI refreshes
                    # match by external id and we don't create duplicates.
                    if str(game.external_game_id).startswith("espn:") and external_game_id not in existing_by_external:
                        game.external_game_id = external_game_id
                    existing_by_external[external_game_id] = game
                else:
                    phase, stage, round_val = _event_season_phase(event)
                    game = Game(
                        external_game_id=external_game_id,
                        sport=sport_config.code,
                        home_team=home_team,
                        away_team=away_team,
                        start_time=commence_time,
                        status="scheduled",
                        season_phase=phase,
                        stage=stage,
                        round_=round_val,
                        canonical_match_key=canonical_key_to_string(match_key),
                    )
                    self._db.add(game)
                    await self._db.flush()  # get game ID
                    existing_by_external[external_game_id] = game
                    existing_by_match[match_key] = game

            # Keep core fields fresh (status may change between fetches)
            # Only update team names if they're not placeholders (extracted names are already set in home_team/away_team)
            placeholder_names_check = {"TBD", "TBA", "TBC", "AFC", "NFC", "TO BE DETERMINED", "TO BE ANNOUNCED"}
            if home_team.upper() not in placeholder_names_check and away_team.upper() not in placeholder_names_check:
                game.home_team = home_team
                game.away_team = away_team
            # If still placeholders, don't overwrite existing - let ESPN fallback or _fix_placeholder_team_names handle it
            game.start_time = commence_time
            # Normalize any upstream status (ESPN placeholders often store STATUS_SCHEDULED).
            game.status = GameStatusNormalizer.normalize(getattr(game, "status", None))
            # Season phase from provider (description/group); never from date
            phase, stage, round_val = _event_season_phase(event)
            if phase is not None:
                game.season_phase = phase
            if stage is not None:
                game.stage = stage
            if round_val is not None:
                game.round_ = round_val

            # Process bookmakers (limit to first 3 books for speed, but process all for player props)
            bookmakers = event.get("bookmakers") or []
            # For player props, we need to check all bookmakers to find FanDuel/DraftKings
            # For other markets, limit to first 3 for speed
            if any("player_props" in str(m.get("key", "")) for b in bookmakers for m in b.get("markets", [])):
                # If player props are present, process all bookmakers to find FanDuel/DraftKings
                bookmakers_to_process = bookmakers
            else:
                # For regular markets, limit to first 3 for speed
                bookmakers_to_process = bookmakers[:3]
            
            # Collect all markets and odds to batch process
            markets_to_add: List[Market] = []
            odds_to_add: List[Odds] = []
            odds_to_update: List[Odds] = []
            
            for bookmaker in bookmakers_to_process:
                book_name = str(bookmaker.get("key") or "").lower()
                markets_data = bookmaker.get("markets", []) or []

                for market_data in markets_data:
                    market_type = str(market_data.get("key") or "")
                    if market_type not in sport_config.supported_markets:
                        continue
                    
                    # Filter player props to only FanDuel and DraftKings
                    if market_type == "player_props" and book_name not in PLAYER_PROPS_BOOKS:
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
                        markets_to_add.append(market)

                    # Process outcomes
                    for outcome_data in outcomes[:10]:
                        outcome_name = str(outcome_data.get("name") or "")
                        price_american = outcome_data.get("price", 0)
                        if not price_american:
                            continue

                        decimal_price = self._american_to_decimal(int(price_american))
                        implied_prob = self._decimal_to_implied_prob(decimal_price)

                        # Normalize outcome name
                        if market_type == "h2h":
                            home_norm = self._normalize_team(home_team, sport_config.code)
                            away_norm = self._normalize_team(away_team, sport_config.code)
                            out_norm = self._normalize_team(outcome_name, sport_config.code)

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
                        elif market_type == "player_props":
                            # Player props format: "Player Name Prop Type Over/Under Line"
                            # The Odds API typically provides: name (player + prop description), point (line)
                            point = outcome_data.get("point")
                            if point is not None:
                                # Format: "Player Name Prop Type Over 27.5" or "Player Name Prop Type Under 27.5"
                                outcome = f"{outcome_name} {float(point):.1f}"
                            else:
                                # Fallback: use name as-is if no point value
                                outcome = outcome_name.strip()
                        else:
                            outcome = outcome_name

                        # Only query existing odds if market already exists
                        if market.id:
                            result = await self._db.execute(
                                select(Odds).where(Odds.market_id == market.id).where(Odds.outcome == outcome).limit(1)
                            )
                            existing_odds = result.scalar_one_or_none()

                            formatted_price = f"+{price_american}" if int(price_american) > 0 else str(int(price_american))
                            if existing_odds:
                                existing_odds.price = formatted_price
                                existing_odds.decimal_price = decimal_price
                                existing_odds.implied_prob = implied_prob
                                odds_to_update.append(existing_odds)
                            else:
                                odds = Odds(
                                    market_id=market.id,
                                    outcome=outcome,
                                    price=formatted_price,
                                    decimal_price=decimal_price,
                                    implied_prob=implied_prob,
                                )
                                odds_to_add.append(odds)
                        else:
                            # Market doesn't exist yet, will add odds after market is flushed
                            formatted_price = f"+{price_american}" if int(price_american) > 0 else str(int(price_american))
                            odds = Odds(
                                market_id=None,  # Will be set after market flush
                                outcome=outcome,
                                price=formatted_price,
                                decimal_price=decimal_price,
                                implied_prob=implied_prob,
                            )
                            # Store market reference for later
                            odds._temp_market = market
                            odds._temp_market_type = market_type
                            odds._temp_book = book_name
                            odds_to_add.append(odds)
            
            # Batch add markets, flush to get IDs
            if markets_to_add:
                self._db.add_all(markets_to_add)
                await self._db.flush()
            
            # Now set market_id for odds that were waiting
            for odds in odds_to_add:
                if hasattr(odds, "_temp_market"):
                    # Find the market we just created
                    result = await self._db.execute(
                        select(Market)
                        .where(Market.game_id == game.id)
                        .where(Market.market_type == odds._temp_market_type)
                        .where(Market.book == odds._temp_book)
                        .limit(1)
                    )
                    market = result.scalar_one_or_none()
                    if market:
                        odds.market_id = market.id
                    delattr(odds, "_temp_market")
                    delattr(odds, "_temp_market_type")
                    delattr(odds, "_temp_book")
            
            # Batch add odds
            if odds_to_add:
                self._db.add_all(odds_to_add)

            games.append(game)

        try:
            await self._db.commit()
            await invalidate_after_odds_update(self._db, sport_config.code)
        except IntegrityError:
            await self._db.rollback()
            if not _retry:
                return await self.normalize_and_store_odds(api_data, sport_config, _retry=True)
            raise
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

    def _normalize_team(self, name: str, sport: Optional[str] = None) -> str:
        return self._team_normalizer.normalize(name, sport=sport)


