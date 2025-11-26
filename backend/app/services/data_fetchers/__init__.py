"""Data fetcher services for external APIs"""

from .nfl_stats import NFLStatsFetcher
from .weather import WeatherFetcher
from .injuries import InjuryFetcher

__all__ = ["NFLStatsFetcher", "WeatherFetcher", "InjuryFetcher"]

