def test_get_available_weeks_does_not_crash():
    """
    Regression: ensure the NFL week helper imports and runs without syntax/indentation errors.
    """
    from app.utils.nfl_week import get_available_weeks

    weeks = get_available_weeks()
    assert isinstance(weeks, list)
    assert len(weeks) > 0


