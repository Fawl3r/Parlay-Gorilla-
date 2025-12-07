"""Data fetcher services for external APIs"""

from .nfl_stats import NFLStatsFetcher
from .weather import WeatherFetcher
from .injuries import InjuryFetcher
from .fetch_utils import RateLimitedFetcher, InMemoryCache, RateLimiter, cached

# SportsRadar fetchers
from .sportsradar_base import SportsRadarBase
from .sportsradar_nfl import SportsRadarNFL, get_nfl_fetcher
from .sportsradar_nba import SportsRadarNBA, get_nba_fetcher
from .sportsradar_nhl import SportsRadarNHL, get_nhl_fetcher
from .sportsradar_mlb import SportsRadarMLB, get_mlb_fetcher
from .sportsradar_soccer import SportsRadarSoccer, get_soccer_fetcher, get_epl_fetcher, get_mls_fetcher
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
    
    # SportsRadar base
    "SportsRadarBase",
    
    # Sport-specific fetchers
    "SportsRadarNFL",
    "SportsRadarNBA", 
    "SportsRadarNHL",
    "SportsRadarMLB",
    "SportsRadarSoccer",
    
    # Factory functions
    "get_nfl_fetcher",
    "get_nba_fetcher",
    "get_nhl_fetcher",
    "get_mlb_fetcher",
    "get_soccer_fetcher",
    "get_epl_fetcher",
    "get_mls_fetcher",
    
    # ESPN scraper
    "ESPNScraper",
    "get_espn_scraper",
]

