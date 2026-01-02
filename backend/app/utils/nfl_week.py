"""NFL week calculation utility"""

from datetime import datetime, date, timedelta, timezone
from typing import Optional, List, Tuple


def get_current_nfl_week(season_year: Optional[int] = None) -> Optional[int]:
    """
    Get the current NFL week based on today's date.
    
    NFL weeks run Tuesday to Monday (games Thu-Sun, MNF on Monday).
    After Monday Night Football ends (Tuesday), we advance to the next week.
    
    Returns:
        Current week number (1-18 for regular season, 19+ for postseason), or None if before season start
    """
    now = datetime.now(timezone.utc)
    calculated_week = calculate_nfl_week(now, season_year)
    
    if calculated_week is None:
        return None
    
    # Check if we're past Monday Night Football for this week
    # NFL weeks end on Monday, so on Tuesday we should advance to next week
    week_start, week_end = get_week_date_range(calculated_week, season_year)
    
    # Find the Monday of this week (NFL weeks end on Monday after MNF)
    # Monday is weekday 0
    days_to_monday = (0 - week_start.weekday()) % 7
    if days_to_monday == 0 and week_start.weekday() != 0:
        days_to_monday = 7
    monday_of_week = week_start + timedelta(days=days_to_monday)
    
    # Monday Night Football typically ends around 11:30 PM ET (3:30 AM UTC next day)
    # So on Tuesday at 4 AM UTC or later, we're in the next week
    monday_end = monday_of_week + timedelta(days=1, hours=4)  # Tuesday 4 AM UTC
    
    if now >= monday_end:
        # We're past MNF, advance to next week
        if calculated_week < 18:
            return calculated_week + 1
        elif calculated_week == 18:
            # Regular season ended, check if we're in postseason
            return get_postseason_week(now, season_year)
    
    return calculated_week


def get_postseason_week(now: datetime, season_year: Optional[int] = None) -> Optional[int]:
    """
    Get the postseason week number.
    
    NFL Postseason structure:
    - Week 19: Wild Card Round (first weekend after Week 18)
    - Week 20: Divisional Round
    - Week 21: Conference Championships
    - Week 22: Super Bowl
    
    Returns:
        Postseason week number (19-22), or None if not in postseason
    """
    if season_year is None:
        if now.month <= 3:
            season_year = now.year - 1
        else:
            season_year = now.year
    
    # Regular season ends after Week 18
    week18_start, week18_end = get_week_date_range(18, season_year)
    
    # Week 18 ends on Monday, postseason starts the following weekend
    # Find the Monday of Week 18
    days_to_monday = (0 - week18_start.weekday()) % 7
    if days_to_monday == 0 and week18_start.weekday() != 0:
        days_to_monday = 7
    monday_week18 = week18_start + timedelta(days=days_to_monday)
    
    # Postseason starts the Saturday after Week 18 ends (Tuesday after MNF)
    postseason_start = monday_week18 + timedelta(days=1, hours=4)  # Tuesday 4 AM UTC
    
    if now < postseason_start:
        return None  # Still in regular season
    
    # Calculate which postseason week
    days_since_postseason = (now.date() - postseason_start.date()).days
    
    # Wild Card: Days 0-6 (Saturday to Monday)
    # Divisional: Days 7-13
    # Conference: Days 14-20
    # Super Bowl: Days 21-27 (usually)
    
    if days_since_postseason <= 6:
        return 19  # Wild Card
    elif days_since_postseason <= 13:
        return 20  # Divisional
    elif days_since_postseason <= 20:
        return 21  # Conference Championships
    elif days_since_postseason <= 27:
        return 22  # Super Bowl
    else:
        return None  # Postseason ended


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
        now = datetime.now(timezone.utc)
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
    
    # Convert to datetime with time, using UTC timezone for consistency
    week_start = datetime.combine(week_start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    week_end = datetime.combine(week_end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
    
    return week_start, week_end


def get_available_weeks(season_year: Optional[int] = None) -> List[dict]:
    """
    Get list of available weeks with their status.
    
    Only shows weeks that are current or future (not past).
    After Monday Night Football, previous weeks are no longer available.
    
    Returns:
        List of dicts with week info: {week, label, is_current, is_available, start_date, end_date}
    """
    current_week = get_current_nfl_week(season_year)
    now = datetime.now(timezone.utc)
    
    if current_week is None:
        # Before season start, return weeks 1-4 as preview
        return [
            {"week": w, "label": f"Week {w}", "is_current": False, "is_available": False}
            for w in range(1, 5)
        ]
    
    weeks = []
    
    # Regular season weeks (1-18)
    for w in range(1, 19):
        week_start, week_end = get_week_date_range(w, season_year)
        
        # Check if this week is past (after Monday Night Football)
        # Find the Monday of this week
        days_to_monday = (0 - week_start.weekday()) % 7
        if days_to_monday == 0 and week_start.weekday() != 0:
            days_to_monday = 7
        monday_of_week = week_start + timedelta(days=days_to_monday)
        
        # Week ends Tuesday 4 AM UTC after MNF
        week_ends = monday_of_week + timedelta(days=1, hours=4)
        
        is_current = (w == current_week)
        is_past = now >= week_ends
        
        # Week is available if it's current or future (not past), and within 2 weeks ahead
        is_available = not is_past and (current_week <= w <= current_week + 2)
        
        weeks.append({
            "week": w,
            "label": f"Week {w}",
            "is_current": is_current,
            "is_available": is_available,
            "start_date": week_start.isoformat(),
            "end_date": week_end.isoformat(),
        })
    
    # Postseason weeks (19-22)
    if current_week and current_week >= 19:
        postseason_labels = {
            19: "Wild Card",
            20: "Divisional",
            21: "Conference Championships",
            22: "Super Bowl"
        }
        
        for w in range(19, 23):
            # Calculate postseason week dates
            week18_start, week18_end = get_week_date_range(18, season_year)
            days_to_monday = (0 - week18_start.weekday()) % 7
            if days_to_monday == 0 and week18_start.weekday() != 0:
                days_to_monday = 7
            monday_week18 = week18_start + timedelta(days=days_to_monday)
            
            postseason_start = monday_week18 + timedelta(days=1, hours=4)
            week_offset = (w - 19) * 7
            week_start = postseason_start + timedelta(days=week_offset)
            week_end = week_start + timedelta(days=7)
            
            is_current = (w == current_week)
            is_past = now >= week_end
            is_available = not is_past and (current_week <= w <= current_week + 2)
            
            weeks.append({
                "week": w,
                "label": postseason_labels.get(w, f"Postseason Week {w}"),
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
    # Weeks 19+ are postseason (handled separately)
    if week > 18:
        # Check if we're in postseason
        postseason_week = get_postseason_week(game_date, season_year)
        if postseason_week:
            return postseason_week
        # Otherwise, it's after season or next season
        return None
    
    return week

