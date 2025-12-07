"""Stats scraper service for team data, weather, and injuries"""

import httpx
import asyncio
from typing import Dict, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json

from app.core.config import settings
from app.models.team_stats import TeamStats
from app.models.game import Game


class StatsScraperService:
    """Service for scraping and aggregating team statistics, weather, and injury data"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.weather_api_key = settings.openweather_api_key
        self._cache: Dict[str, tuple] = {}  # Simple in-memory cache: key -> (data, timestamp)
        self._cache_ttl = 3600  # 1 hour cache
    
    async def get_team_stats(
        self,
        team_name: str,
        season: str,
        week: Optional[int] = None
    ) -> Optional[Dict]:
        """
        Get team statistics from database or calculate from game results
        
        Returns dict with:
        - Record (wins, losses, win_pct)
        - Offensive stats (ppg, ypg, etc.)
        - Defensive stats (papg, yapg, etc.)
        - ATS trends (ats_wins, ats_losses, ats_pct)
        - O/U trends (over_wins, under_wins, over_pct)
        - Recent form (last 5 games)
        """
        cache_key = f"team_stats:{team_name}:{season}:{week or 'season'}"
        
        # Check cache
        if cache_key in self._cache:
            data, timestamp = self._cache[cache_key]
            if (datetime.now() - timestamp).total_seconds() < self._cache_ttl:
                return data
        
        # Query database
        query = select(TeamStats).where(
            TeamStats.team_name == team_name,
            TeamStats.season == season
        )
        if week:
            query = query.where(TeamStats.week == week)
        else:
            query = query.where(TeamStats.week.is_(None))
        
        result = await self.db.execute(query)
        team_stats = result.scalar_one_or_none()
        
        if team_stats:
            stats_dict = {
                "team_name": team_stats.team_name,
                "season": team_stats.season,
                "week": team_stats.week,
                "record": {
                    "wins": team_stats.wins,
                    "losses": team_stats.losses,
                    "ties": team_stats.ties,
                    "win_percentage": team_stats.win_percentage,
                },
                "offense": {
                    "points_per_game": team_stats.points_per_game,
                    "yards_per_game": team_stats.yards_per_game,
                    "passing_yards_per_game": team_stats.passing_yards_per_game,
                    "rushing_yards_per_game": team_stats.rushing_yards_per_game,
                },
                "defense": {
                    "points_allowed_per_game": team_stats.points_allowed_per_game,
                    "yards_allowed_per_game": team_stats.yards_allowed_per_game,
                    "turnovers_forced": team_stats.turnovers_forced,
                },
                "recent_form": {
                    "recent_wins": team_stats.recent_wins,
                    "recent_losses": team_stats.recent_losses,
                    "home_record": f"{team_stats.home_record_wins}-{team_stats.home_record_losses}",
                    "away_record": f"{team_stats.away_record_wins}-{team_stats.away_record_losses}",
                },
                "strength_ratings": {
                    "offensive_rating": team_stats.offensive_rating,
                    "defensive_rating": team_stats.defensive_rating,
                    "overall_rating": team_stats.overall_rating,
                },
                "ats_trends": {
                    "wins": team_stats.ats_wins,
                    "losses": team_stats.ats_losses,
                    "pushes": team_stats.ats_pushes,
                    "win_percentage": team_stats.ats_win_percentage,
                    "recent": f"{team_stats.ats_recent_wins}-{team_stats.ats_recent_losses}",
                    "home": f"{team_stats.ats_home_wins}-{team_stats.ats_home_losses}",
                    "away": f"{team_stats.ats_away_wins}-{team_stats.ats_away_losses}",
                },
                "over_under_trends": {
                    "overs": team_stats.over_wins,
                    "unders": team_stats.under_wins,
                    "over_percentage": team_stats.over_percentage,
                    "recent_overs": team_stats.over_recent_count,
                    "recent_unders": team_stats.under_recent_count,
                    "avg_total_points": team_stats.avg_total_points,
                },
            }
            
            # Cache it
            self._cache[cache_key] = (stats_dict, datetime.now())
            return stats_dict
        
        # Return None if not found (will be calculated from game results later)
        return None
    
    async def get_weather_data(
        self,
        city: str,
        state: str,
        game_time: datetime
    ) -> Optional[Dict]:
        """
        Get weather data for outdoor games (NFL, MLB)
        
        Returns dict with:
        - temperature
        - conditions (rain, snow, wind, etc.)
        - wind_speed
        - precipitation_probability
        - impact_assessment (how weather affects the game)
        """
        if not self.weather_api_key:
            return None
        
        cache_key = f"weather:{city}:{state}:{game_time.date()}"
        
        # Check cache
        if cache_key in self._cache:
            data, timestamp = self._cache[cache_key]
            if (datetime.now() - timestamp).total_seconds() < 7200:  # 2 hour cache for weather
                return data
        
        try:
            # Use OpenWeatherMap API (free tier: 1000 calls/day)
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Get lat/lon from city name (simplified - in production use geocoding)
                # For now, use a simple mapping or geocoding API
                response = await client.get(
                    "https://api.openweathermap.org/data/2.5/weather",
                    params={
                        "q": f"{city},{state},US",
                        "appid": self.weather_api_key,
                        "units": "imperial"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    weather_dict = {
                        "temperature": data.get("main", {}).get("temp"),
                        "feels_like": data.get("main", {}).get("feels_like"),
                        "conditions": data.get("weather", [{}])[0].get("main", "").lower(),
                        "description": data.get("weather", [{}])[0].get("description", ""),
                        "wind_speed": data.get("wind", {}).get("speed", 0),
                        "wind_direction": data.get("wind", {}).get("deg", 0),
                        "humidity": data.get("main", {}).get("humidity"),
                        "precipitation_probability": 0,  # Not in current weather API
                        "impact_assessment": self._assess_weather_impact(data),
                    }
                    
                    # Cache it
                    self._cache[cache_key] = (weather_dict, datetime.now())
                    return weather_dict
        except Exception as e:
            print(f"[StatsScraper] Weather fetch error: {e}")
        
        return None
    
    def _assess_weather_impact_from_data(self, weather_data: Dict) -> str:
        """Assess weather impact from weather fetcher data"""
        impacts = []
        temp = weather_data.get("temperature", 70)
        wind_speed = weather_data.get("wind_speed", 0)
        condition = weather_data.get("condition", "clear").lower()
        precipitation = weather_data.get("precipitation", 0)
        
        if condition in ["rain", "snow", "thunderstorm"]:
            impacts.append(f"{condition.capitalize()} conditions will significantly impact passing and ball handling")
        elif precipitation > 0:
            impacts.append(f"Precipitation expected, which may affect field conditions and passing accuracy")
        
        if wind_speed > 20:
            impacts.append(f"Strong winds ({wind_speed} mph) will heavily impact deep passing and field goal attempts")
        elif wind_speed > 15:
            impacts.append(f"Moderate to strong winds ({wind_speed} mph) may affect deep passes and kicking game")
        elif wind_speed > 10:
            impacts.append(f"Moderate winds ({wind_speed} mph) may slightly impact deep passes")
        
        if temp < 32:
            impacts.append("Freezing temperatures may affect ball handling and player performance")
        elif temp > 85:
            impacts.append("Hot conditions may lead to fatigue in later quarters")
        
        return ". ".join(impacts) if impacts else "Weather conditions should not significantly impact gameplay"
    
    def _assess_weather_impact(self, weather_data: Dict) -> str:
        """Assess how weather conditions might impact the game"""
        conditions = weather_data.get("weather", [{}])[0].get("main", "").lower()
        wind_speed = weather_data.get("wind", {}).get("speed", 0)
        temp = weather_data.get("main", {}).get("temp", 70)
        
        impacts = []
        
        if conditions in ["rain", "drizzle"]:
            impacts.append("Wet conditions favor running game and may reduce passing efficiency")
        elif conditions in ["snow"]:
            impacts.append("Snow significantly impacts passing and kicking games")
        
        if wind_speed > 15:
            impacts.append(f"Strong winds ({wind_speed} mph) will affect passing and kicking")
        elif wind_speed > 10:
            impacts.append(f"Moderate winds ({wind_speed} mph) may slightly impact deep passes")
        
        if temp < 32:
            impacts.append("Freezing temperatures may affect ball handling and player performance")
        elif temp > 85:
            impacts.append("Hot conditions may lead to fatigue in later quarters")
        
        return ". ".join(impacts) if impacts else "Weather conditions should not significantly impact gameplay"
    
    async def get_injury_report(
        self,
        team_name: str,
        league: str
    ) -> Optional[Dict]:
        """
        Get injury report for a team
        
        Returns dict with:
        - key_players_out (list of important players)
        - injury_summary (text summary)
        - impact_assessment (how injuries affect team)
        """
        # Note: Real injury data requires paid APIs or scraping (which has ToS issues)
        # For now, return a placeholder structure that can be filled by game results analysis
        
        cache_key = f"injuries:{team_name}:{league}"
        
        # Check cache
        if cache_key in self._cache:
            data, timestamp = self._cache[cache_key]
            if (datetime.now() - timestamp).total_seconds() < 3600:  # 1 hour cache
                return data
        
        # Placeholder - in production, integrate with injury API or scrape (respecting ToS)
        injury_dict = {
            "key_players_out": [],
            "injury_summary": "Injury data not available. Check official team sources for latest updates.",
            "impact_assessment": "Unable to assess injury impact without current data.",
        }
        
        # Cache it
        self._cache[cache_key] = (injury_dict, datetime.now())
        return injury_dict
    
    async def get_matchup_data(
        self,
        home_team: str,
        away_team: str,
        league: str,
        season: str,
        game_time: datetime
    ) -> Dict:
        """
        Get comprehensive matchup data for both teams
        
        Returns dict with:
        - home_team_stats
        - away_team_stats
        - head_to_head (if available)
        - weather (if outdoor game)
        - injuries (both teams)
        """
        # Get stats for both teams
        home_stats = await self.get_team_stats(home_team, season)
        away_stats = await self.get_team_stats(away_team, season)
        
        # Get weather for outdoor games (NFL, MLB)
        weather = None
        if league in ["NFL", "MLB"]:
            try:
                from app.services.data_fetchers.weather import WeatherFetcher
                weather_fetcher = WeatherFetcher()
                weather_data = await weather_fetcher.get_game_weather(
                    home_team=home_team,
                    game_time=game_time
                )
                if weather_data:
                    weather = {
                        "temperature": weather_data.get("temperature", 0),
                        "feels_like": weather_data.get("feels_like", 0),
                        "description": weather_data.get("description", weather_data.get("condition", "clear")),
                        "wind_speed": weather_data.get("wind_speed", 0),
                        "wind_direction": weather_data.get("wind_direction", 0),
                        "humidity": weather_data.get("humidity", 0),
                        "precipitation": weather_data.get("precipitation", 0),
                        "condition": weather_data.get("condition", "clear"),
                        "is_outdoor": weather_data.get("is_outdoor", True),
                        "affects_game": weather_data.get("affects_game", False),
                        "impact_assessment": self._assess_weather_impact_from_data(weather_data)
                    }
            except Exception as e:
                print(f"[StatsScraper] Error fetching weather: {e}")
                weather = None
        
        # Get injuries
        home_injuries = await self.get_injury_report(home_team, league)
        away_injuries = await self.get_injury_report(away_team, league)
        
        return {
            "home_team_stats": home_stats,
            "away_team_stats": away_stats,
            "weather": weather,
            "home_injuries": home_injuries,
            "away_injuries": away_injuries,
            "head_to_head": None,  # Can be added later from game results
        }
    
    def clear_cache(self):
        """Clear the in-memory cache"""
        self._cache.clear()

