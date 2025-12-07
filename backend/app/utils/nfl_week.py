"""NFL week calculation utility"""

from datetime import datetime, date, timedelta
from typing import Optional, List, Tuple


def get_current_nfl_week(season_year: Optional[int] = None) -> Optional[int]:
    """
    Get the current NFL week based on today's date.
    
    Returns:
        Current week number (1-18), or None if before season start
    """
    return calculate_nfl_week(datetime.now(), season_year)


def get_week_date_range(week: int, season_year: Optional[int] = None) -> Tuple[datetime, datetime]:
    """
    Get the start and end datetime for a given NFL week.
    
    Args:
        week: NFL week number (1-18)
        season_year: The season year
        
    Returns:
        Tuple of (week_start, week_end) datetimes
    """
    if season_year is None:
        # Determine season year based on current date
        now = datetime.now()
        # If we're in January-March, it's the previous year's season
        if now.month <= 3:
            season_year = now.year - 1
        else:
            season_year = now.year
    
    # Get season start
    season_starts = {
        2024: date(2024, 9, 5),
        2025: date(2025, 9, 4),
        2026: date(2026, 9, 10),
    }
    
    if season_year not in season_starts:
        sept_1 = date(season_year, 9, 1)
        days_until_thursday = (3 - sept_1.weekday()) % 7
        if days_until_thursday == 0:
            season_start = sept_1
        else:
            season_start = date(season_year, 9, 1 + days_until_thursday)
    else:
        season_start = season_starts[season_year]
    
    # Calculate week start (week 1 starts at day 0)
    week_start_date = season_start + timedelta(days=(week - 1) * 7)
    week_end_date = week_start_date + timedelta(days=7)
    
    # Convert to datetime with time
    week_start = datetime.combine(week_start_date, datetime.min.time())
    week_end = datetime.combine(week_end_date, datetime.max.time())
    
    return week_start, week_end


def get_available_weeks(season_year: Optional[int] = None) -> List[dict]:
    """
    Get list of available weeks with their status.
    
    Returns:
        List of dicts with week info: {week, label, is_current, start_date, end_date}
    """
    current_week = get_current_nfl_week(season_year)
    
    if current_week is None:
        # Before season start, return weeks 1-4 as preview
        return [
            {"week": w, "label": f"Week {w}", "is_current": False, "is_available": False}
            for w in range(1, 5)
        ]
    
    weeks = []
    for w in range(1, 19):  # 18 regular season weeks
        week_start, week_end = get_week_date_range(w, season_year)
        is_current = (w == current_week)
        # Week is available if it's current week or a future week (up to 2 weeks ahead)
        is_available = (current_week <= w <= current_week + 2)
        
        weeks.append({
            "week": w,
            "label": f"Week {w}",
            "is_current": is_current,
            "is_available": is_available,
            "start_date": week_start.isoformat(),
            "end_date": week_end.isoformat(),
        })
    
    return weeks


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

