"""Convert ORM Game objects into API response schemas.

Split out of OddsFetcherService to keep services small and focused.
"""

from __future__ import annotations

from typing import List

from app.models.game import Game
from app.schemas.game import GameResponse
from app.utils.nfl_week import calculate_nfl_week
from app.utils.timezone_utils import TimezoneNormalizer


class GameResponseConverter:
    """Converts `Game` ORM models (with markets/odds loaded) into `GameResponse`."""

    def to_response(self, games: List[Game]) -> List[GameResponse]:
        result: List[GameResponse] = []
        for game in games:
            # Filter out games with TBD team names (shouldn't happen if data store filters correctly, but safety check)
            if (game.home_team and game.home_team.upper() == "TBD") or (game.away_team and game.away_team.upper() == "TBD"):
                continue
            week = calculate_nfl_week(game.start_time) if game.sport == "NFL" else None

            normalized_start = TimezoneNormalizer.ensure_utc(game.start_time)
            game_dict = {
                "id": str(game.id),
                "external_game_id": game.external_game_id,
                "sport": game.sport,
                "home_team": game.home_team,
                "away_team": game.away_team,
                "start_time": normalized_start,
                "status": game.status,
                "week": week,
                "home_score": getattr(game, "home_score", None),
                "away_score": getattr(game, "away_score", None),
                "markets": [
                    {
                        "id": str(market.id),
                        "market_type": market.market_type,
                        "book": market.book,
                        "odds": [
                            {
                                "id": str(odd.id),
                                "outcome": odd.outcome,
                                "price": odd.price,
                                "decimal_price": float(odd.decimal_price),
                                "implied_prob": float(odd.implied_prob),
                                "created_at": TimezoneNormalizer.isoformat_utc(odd.created_at),
                            }
                            for odd in self._sorted_odds(market_type=str(market.market_type or ""), odds=list(market.odds or []))
                        ],
                    }
                    for market in game.markets
                ],
            }
            result.append(GameResponse.model_validate(game_dict))
        return result

    @staticmethod
    def _sorted_odds(*, market_type: str, odds: List) -> List:
        """
        Return stable odds ordering for consumers.

        - `h2h` can have a third outcome for soccer (draw). Keep home/away first.
        """
        if (market_type or "").lower() != "h2h":
            return odds

        priority = {"home": 0, "away": 1, "draw": 2, "tie": 2}
        return sorted(odds, key=lambda o: priority.get(str(getattr(o, "outcome", "") or "").lower(), 99))



