"""NFL week calculation utility"""

from datetime import datetime, date
from typing import Optional


def calculate_nfl_week(game_date: datetime, season_year: Optional[int] = None) -> Optional[int]:
    """
    Calculate NFL week number from a game date.
    
    NFL season typically starts in early September (around Sept 5-9).
    Each week runs from Tuesday to Monday (games typically Thu-Sun).
    
    Args:
        game_date: The game start time/date
        season_year: The season year (e.g., 2024). If None, uses game_date.year
    
    Returns:
        Week number (1-18 for regular season, or None if before season start)
    """
    if season_year is None:
        season_year = game_date.year
    
    # Convert to date if datetime
    if isinstance(game_date, datetime):
        game_date = game_date.date()
    
    # NFL season typically starts in early September
    # Week 1 usually starts around September 5-9 (first Thursday after Labor Day)
    # NFL weeks run Tuesday to Monday, but Week 1 typically starts on Thursday
    
    # Determine season start date
    # For 2024 season: Week 1 starts Sept 5, 2024 (Thursday)
    # For 2025 season: Week 1 starts Sept 4, 2025 (Thursday) 
    # For 2026 season: Week 1 starts Sept 10, 2026 (Thursday)
    
    # Use a lookup table for known seasons, with fallback calculation
    season_starts = {
        2024: date(2024, 9, 5),   # Week 1 start (Thursday)
        2025: date(2025, 9, 4),   # Week 1 start (Thursday)
        2026: date(2026, 9, 10),  # Week 1 start (Thursday)
    }
    
    # If we don't have the exact start, estimate: first Thursday of September
    # (NFL typically starts the first Thursday after Labor Day, which is first Monday of Sept)
    if season_year not in season_starts:
        # Find first Thursday of September
        sept_1 = date(season_year, 9, 1)
        # Thursday is weekday 3 (0=Monday, 3=Thursday)
        days_until_thursday = (3 - sept_1.weekday()) % 7
        if days_until_thursday == 0:
            # If Sept 1 is Thursday, that's Week 1
            season_start = sept_1
        else:
            season_start = date(season_year, 9, 1 + days_until_thursday)
    else:
        season_start = season_starts[season_year]
    
    # If game is before season start, return None
    if game_date < season_start:
        return None
    
    # Calculate days since season start
    days_since_start = (game_date - season_start).days
    
    # Calculate week number (1-indexed)
    # Each week is 7 days from the season start
    # Week 1: Days 0-6, Week 2: Days 7-13, etc.
    week = (days_since_start // 7) + 1
    
    # Regular season is 18 weeks
    if week > 18:
        # Could be playoffs or next season
        # For simplicity, cap at 18 for regular season
        return 18
    
    return week

