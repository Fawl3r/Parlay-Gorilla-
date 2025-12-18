from __future__ import annotations

from datetime import date, datetime

from app.database.session import AsyncSessionLocal
from app.services.ats_ou_calculator import ATSOUCalculator


class AtsOuTrendsJob:
    """Compute ATS / O/U trends across supported sports (daily)."""

    async def run(self) -> None:
        async with AsyncSessionLocal() as db:
            try:
                current_year = datetime.now().year
                season = str(current_year)

                sports_config = [
                    ("NFL", "REG", None, None, None),
                    ("NBA", "REG", None, None, None),
                    ("NHL", "REG", None, None, None),
                    ("MLB", "REG", None, date(current_year, 3, 1), date(current_year, 11, 1)),
                ]

                total_games = 0
                total_teams = 0

                for sport, season_type, weeks, start_date, end_date in sports_config:
                    try:
                        calculator = ATSOUCalculator(db, sport=sport)

                        if sport in ["NFL", "NBA", "NHL"]:
                            result = await calculator.calculate_season_trends(
                                season=season,
                                season_type=season_type,
                                weeks=weeks,
                            )
                        else:
                            result = await calculator.calculate_season_trends(
                                season=season,
                                season_type=season_type,
                                start_date=start_date,
                                end_date=end_date,
                            )

                        games = result.get("games_processed", 0)
                        teams = result.get("teams_updated", 0)
                        total_games += games
                        total_teams += teams

                        if games > 0:
                            print(f"[SCHEDULER] {sport}: {games} games, {teams} teams updated")
                    except Exception as sport_error:
                        print(f"[SCHEDULER] Error calculating ATS/O/U for {sport}: {sport_error}")
                        continue

                print(
                    f"[SCHEDULER] ATS/O/U trends calculated: {total_games} games, {total_teams} teams across all sports"
                )
            except Exception as e:
                print(f"[SCHEDULER] Error calculating ATS/O/U trends: {e}")
                import traceback

                traceback.print_exc()



