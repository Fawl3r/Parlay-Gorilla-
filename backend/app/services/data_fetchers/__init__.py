"""Data fetcher services for external APIs"""

from .nfl_stats import NFLStatsFetcher
from .weather import WeatherFetcher
from .injuries import InjuryFetcher
from .fetch_utils import RateLimitedFetcher, InMemoryCache, RateLimiter, cached
from .espn_scraper import ESPNScraper, get_espn_scraper

__all__ = [
    # Legacy fetchers
    "NFLStatsFetcher",
    "WeatherFetcher",
    "InjuryFetcher",
    # Utilities
    "RateLimitedFetcher",
    "InMemoryCache",
    "RateLimiter",
    "cached",
    # ESPN scraper (fallback for stats/results when API-Sports unavailable)
    "ESPNScraper",
    "get_espn_scraper",
]

