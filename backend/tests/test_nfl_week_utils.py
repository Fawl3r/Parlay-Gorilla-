def test_get_available_weeks_does_not_crash():
    """
    Regression: ensure the NFL week helper imports and runs without syntax/indentation errors.
    """
    from app.utils.nfl_week import get_available_weeks

    weeks = get_available_weeks()
    assert isinstance(weeks, list)
    assert len(weeks) > 0


def test_calculate_nfl_week_in_january_uses_previous_season_year():
    """
    Regression: January dates belong to the previous season (Sep -> Feb).

    Example: 2026-01-02 should map to the 2025 season and produce a regular-season week
    (not None due to using 2026 season start).
    """
    from datetime import datetime, timezone

    from app.utils.nfl_week import calculate_nfl_week

    week = calculate_nfl_week(datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc))
    assert week == 18


def test_calculate_nfl_week_accepts_date_like_inputs():
    """
    Some call sites pass date-only values. Ensure we still compute the correct week and don't crash.
    """
    from datetime import date

    from app.utils.nfl_week import calculate_nfl_week

    week = calculate_nfl_week(date(2026, 1, 2))
    assert week == 18


