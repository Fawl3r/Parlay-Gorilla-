"""
Tests for API-Sports date-aware season resolver.

Covers cross-year seasons: NFL/NHL/soccer Jan–Feb → previous season start year,
NBA Oct–June ranges, and wrapper behavior.
"""

from datetime import datetime, timezone

import pytest

from app.services.apisports.season_resolver import (
    get_season_for_sport,
    get_season_for_sport_at_date,
    get_season_int_for_sport,
    get_season_int_for_sport_at_date,
)


class TestGetSeasonForSportAtDate:
    """get_season_for_sport_at_date(sport, dt) behavior."""

    def test_nfl_jan_feb_previous_season_start_year(self) -> None:
        # Jan/Feb = still in season that started previous calendar year
        jan_15_2025 = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        assert get_season_for_sport_at_date("nfl", jan_15_2025) == "2024"
        assert get_season_for_sport_at_date("americanfootball_nfl", jan_15_2025) == "2024"
        feb_1_2025 = datetime(2025, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        assert get_season_for_sport_at_date("nfl", feb_1_2025) == "2024"

    def test_nfl_sep_dec_current_year(self) -> None:
        sep_15_2025 = datetime(2025, 9, 15, 12, 0, 0, tzinfo=timezone.utc)
        assert get_season_for_sport_at_date("nfl", sep_15_2025) == "2025"
        dec_1_2024 = datetime(2024, 12, 1, 12, 0, 0, tzinfo=timezone.utc)
        assert get_season_for_sport_at_date("nfl", dec_1_2024) == "2024"

    def test_nhl_jan_feb_previous_season_start_year(self) -> None:
        jan_15_2025 = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        assert get_season_for_sport_at_date("nhl", jan_15_2025) == "2024"
        assert get_season_for_sport_at_date("icehockey_nhl", jan_15_2025) == "2024"
        feb_28_2025 = datetime(2025, 2, 28, 12, 0, 0, tzinfo=timezone.utc)
        assert get_season_for_sport_at_date("nhl", feb_28_2025) == "2024"

    def test_nhl_oct_dec_current_year(self) -> None:
        oct_15_2024 = datetime(2024, 10, 15, 12, 0, 0, tzinfo=timezone.utc)
        assert get_season_for_sport_at_date("nhl", oct_15_2024) == "2024"
        dec_1_2024 = datetime(2024, 12, 1, 12, 0, 0, tzinfo=timezone.utc)
        assert get_season_for_sport_at_date("nhl", dec_1_2024) == "2024"

    def test_soccer_jan_jul_previous_season_start_year(self) -> None:
        jan_15_2025 = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        assert get_season_for_sport_at_date("football", jan_15_2025) == "2024"
        assert get_season_for_sport_at_date("soccer", jan_15_2025) == "2024"
        may_1_2025 = datetime(2025, 5, 1, 12, 0, 0, tzinfo=timezone.utc)
        assert get_season_for_sport_at_date("football", may_1_2025) == "2024"

    def test_soccer_aug_dec_current_year(self) -> None:
        aug_15_2025 = datetime(2025, 8, 15, 12, 0, 0, tzinfo=timezone.utc)
        assert get_season_for_sport_at_date("football", aug_15_2025) == "2025"
        dec_1_2024 = datetime(2024, 12, 1, 12, 0, 0, tzinfo=timezone.utc)
        assert get_season_for_sport_at_date("football", dec_1_2024) == "2024"

    def test_nba_jan_june_previous_start_year_range(self) -> None:
        jan_15_2025 = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        assert get_season_for_sport_at_date("nba", jan_15_2025) == "2024-2025"
        assert get_season_for_sport_at_date("basketball_nba", jan_15_2025) == "2024-2025"
        june_15_2025 = datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        assert get_season_for_sport_at_date("nba", june_15_2025) == "2024-2025"

    def test_nba_oct_dec_current_start_year_range(self) -> None:
        oct_15_2024 = datetime(2024, 10, 15, 12, 0, 0, tzinfo=timezone.utc)
        assert get_season_for_sport_at_date("nba", oct_15_2024) == "2024-2025"
        dec_1_2024 = datetime(2024, 12, 1, 12, 0, 0, tzinfo=timezone.utc)
        assert get_season_for_sport_at_date("nba", dec_1_2024) == "2024-2025"

    def test_mlb_apr_oct_current_year(self) -> None:
        jul_1_2025 = datetime(2025, 7, 1, 12, 0, 0, tzinfo=timezone.utc)
        assert get_season_for_sport_at_date("mlb", jul_1_2025) == "2025"
        apr_1_2025 = datetime(2025, 4, 1, 12, 0, 0, tzinfo=timezone.utc)
        assert get_season_for_sport_at_date("mlb", apr_1_2025) == "2025"

    def test_mlb_jan_mar_previous_year(self) -> None:
        jan_15_2025 = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        assert get_season_for_sport_at_date("mlb", jan_15_2025) == "2024"
        mar_1_2025 = datetime(2025, 3, 1, 12, 0, 0, tzinfo=timezone.utc)
        assert get_season_for_sport_at_date("mlb", mar_1_2025) == "2024"

    def test_naive_datetime_treated_as_utc(self) -> None:
        jan_15_2025_naive = datetime(2025, 1, 15, 12, 0, 0)
        assert get_season_for_sport_at_date("nfl", jan_15_2025_naive) == "2024"
        assert get_season_for_sport_at_date("nhl", jan_15_2025_naive) == "2024"


class TestGetSeasonIntForSportAtDate:
    """get_season_int_for_sport_at_date(sport, dt) behavior."""

    def test_nfl_jan_returns_previous_year_int(self) -> None:
        jan_15_2025 = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        assert get_season_int_for_sport_at_date("nfl", jan_15_2025) == 2024

    def test_nba_returns_first_year_of_range(self) -> None:
        jan_15_2025 = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        assert get_season_int_for_sport_at_date("nba", jan_15_2025) == 2024

    def test_soccer_jan_returns_previous_year_int(self) -> None:
        jan_15_2025 = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        assert get_season_int_for_sport_at_date("football", jan_15_2025) == 2024


class TestWrappersUseNow:
    """get_season_for_sport / get_season_int_for_sport delegate to date-aware with now."""

    def test_get_season_for_sport_returns_string(self) -> None:
        s = get_season_for_sport("nfl")
        assert isinstance(s, str)
        assert s.isdigit() or "-" in s

    def test_get_season_int_for_sport_returns_int(self) -> None:
        n = get_season_int_for_sport("nba")
        assert isinstance(n, int)
        assert n >= 2020
