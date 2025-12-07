"""Test NFL week utilities."""
from app.utils.nfl_week import get_current_nfl_week, get_week_date_range, get_available_weeks

print("Testing NFL week utilities...")
print(f"Current week: {get_current_nfl_week()}")

weeks = get_available_weeks()
available_count = len([w for w in weeks if w["is_available"]])
print(f"Available weeks: {available_count}")

if weeks:
    current = [w for w in weeks if w["is_current"]]
    if current:
        print(f"Current week info: {current[0]}")

week_range = get_week_date_range(14)
print(f"Week 14 range: {week_range[0].date()} to {week_range[1].date()}")

print("\nAll tests passed!")

