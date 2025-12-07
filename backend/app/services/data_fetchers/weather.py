"""Weather data fetcher for game conditions"""

import httpx
from typing import Dict, Optional
from datetime import datetime
from app.core.config import settings


class WeatherFetcher:
    """Fetches weather conditions for game locations using OpenWeatherMap"""
    
    def __init__(self):
        self.api_key = getattr(settings, "openweather_api_key", None)
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.timeout = 10.0
        
        # NFL stadium locations (lat, lon) and type (outdoor/indoor/dome)
        self.stadium_locations = {
            "baltimore": (39.2780, -76.6227),  # M&T Bank Stadium - OUTDOOR
            "kansas city": (39.0489, -94.4839),  # Arrowhead Stadium - OUTDOOR
            "buffalo": (42.7738, -78.7869),  # Highmark Stadium - OUTDOOR
            "miami": (25.9580, -80.2389),  # Hard Rock Stadium - OUTDOOR
            "foxborough": (42.0939, -71.2642),  # Gillette Stadium - OUTDOOR
            "east rutherford": (40.8136, -74.0744),  # MetLife Stadium - OUTDOOR
            "cincinnati": (39.0950, -84.5160),  # Paycor Stadium - OUTDOOR
            "cleveland": (41.5061, -81.6996),  # FirstEnergy Stadium - OUTDOOR
            "pittsburgh": (40.4468, -80.0158),  # Acrisure Stadium - OUTDOOR
            "houston": (29.6847, -95.4107),  # NRG Stadium - RETRACTABLE DOME (indoor)
            "indianapolis": (39.7601, -86.1639),  # Lucas Oil Stadium - RETRACTABLE DOME (indoor)
            "jacksonville": (30.3239, -81.6373),  # TIAA Bank Field - OUTDOOR
            "nashville": (36.1665, -86.7713),  # Nissan Stadium - OUTDOOR
            "denver": (39.7439, -105.0200),  # Empower Field - OUTDOOR
            "los angeles": (34.0141, -118.2879),  # SoFi Stadium - INDOOR
            "las vegas": (36.0908, -115.1837),  # Allegiant Stadium - INDOOR
            "dallas": (32.7473, -97.0945),  # AT&T Stadium - RETRACTABLE DOME (indoor)
            "new york": (40.8136, -74.0744),  # MetLife Stadium - OUTDOOR
            "philadelphia": (39.9008, -75.1675),  # Lincoln Financial Field - OUTDOOR
            "landover": (38.9076, -76.8644),  # FedExField - OUTDOOR
            "chicago": (41.8625, -87.6167),  # Soldier Field - OUTDOOR
            "detroit": (42.3400, -83.0456),  # Ford Field - INDOOR
            "green bay": (44.5013, -88.0622),  # Lambeau Field - OUTDOOR
            "minneapolis": (44.9740, -93.2581),  # U.S. Bank Stadium - INDOOR
            "atlanta": (33.7550, -84.4010),  # Mercedes-Benz Stadium - RETRACTABLE DOME (indoor)
            "charlotte": (35.2258, -80.8528),  # Bank of America Stadium - OUTDOOR
            "new orleans": (29.9511, -90.0815),  # Caesars Superdome - INDOOR
            "tampa": (27.9756, -82.5033),  # Raymond James Stadium - OUTDOOR
            "phoenix": (33.5275, -112.2625),  # State Farm Stadium - RETRACTABLE DOME (indoor)
            "inglewood": (34.0141, -118.2879),  # SoFi Stadium - INDOOR
            "santa clara": (37.4030, -121.9694),  # Levi's Stadium - OUTDOOR
            "seattle": (47.5952, -122.3316),  # Lumen Field - OUTDOOR
        }
        
        # Indoor/retractable dome stadiums (weather doesn't affect these)
        self.indoor_stadiums = {
            "houston",  # NRG Stadium (retractable)
            "indianapolis",  # Lucas Oil Stadium (retractable)
            "dallas",  # AT&T Stadium (retractable)
            "detroit",  # Ford Field (fixed dome)
            "minneapolis",  # U.S. Bank Stadium (fixed dome)
            "atlanta",  # Mercedes-Benz Stadium (retractable)
            "new orleans",  # Caesars Superdome (fixed dome)
            "phoenix",  # State Farm Stadium (retractable)
            "los angeles",  # SoFi Stadium (indoor)
            "las vegas",  # Allegiant Stadium (indoor)
            "inglewood",  # SoFi Stadium (indoor)
        }
    
    async def get_game_weather(
        self,
        home_team: str,
        game_time: datetime,
        location: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get weather forecast for a game
        
        Args:
            home_team: Home team name
            game_time: Scheduled game time
            location: Optional specific location (city name)
            
        Returns:
            Dictionary with weather data or None
        """
        if not self.api_key:
            # Return basic weather estimate if no API key
            return self._get_basic_weather_estimate(home_team, game_time)
        
        try:
            # Get location coordinates
            coords = self._get_stadium_coords(home_team, location)
            if not coords:
                return None
            
            lat, lon = coords
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Get forecast (OpenWeatherMap free tier)
                url = f"{self.base_url}/forecast"
                params = {
                    "lat": lat,
                    "lon": lon,
                    "appid": self.api_key,
                    "units": "imperial",
                }
                
                response = await client.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    weather_data = self._parse_weather_data(data, game_time, home_team)
                    return weather_data
                else:
                    print(f"Weather API error: {response.status_code}")
                    return self._get_basic_weather_estimate(home_team, game_time)
                    
        except Exception as e:
            print(f"Error fetching weather: {e}")
            return self._get_basic_weather_estimate(home_team, game_time)
    
    def _get_stadium_coords(self, team_name: str, location: Optional[str] = None) -> Optional[tuple]:
        """Get stadium coordinates for a team"""
        team_lower = team_name.lower()
        
        # Special team name mappings (e.g., "New York Jets" -> "east rutherford" or "new york")
        team_mappings = {
            "new york jets": "east rutherford",
            "new york giants": "east rutherford",
            "jets": "east rutherford",
            "giants": "east rutherford",
        }
        
        # Check team mappings first
        for team_key, stadium_city in team_mappings.items():
            if team_key in team_lower:
                return self.stadium_locations.get(stadium_city)
        
        # Try direct match
        for city, coords in self.stadium_locations.items():
            if city in team_lower or team_lower in city:
                return coords
        
        # Try location parameter
        if location:
            location_lower = location.lower()
            for city, coords in self.stadium_locations.items():
                if city in location_lower or location_lower in city:
                    return coords
        
        return None
    
    def _parse_weather_data(self, data: Dict, game_time: datetime, team_name: str) -> Dict:
        """Parse OpenWeatherMap forecast data"""
        try:
            forecasts = data.get("list", [])
            
            # Find forecast closest to game time
            closest_forecast = None
            min_diff = float('inf')
            
            for forecast in forecasts:
                forecast_time = datetime.fromtimestamp(forecast.get("dt", 0))
                diff = abs((forecast_time - game_time).total_seconds())
                if diff < min_diff:
                    min_diff = diff
                    closest_forecast = forecast
            
            if closest_forecast:
                main = closest_forecast.get("main", {})
                weather = closest_forecast.get("weather", [{}])[0]
                wind = closest_forecast.get("wind", {})
                
                # Determine if stadium is outdoor
                is_outdoor = self._is_outdoor_stadium(team_name)
                
                return {
                    "temperature": main.get("temp", 0),
                    "feels_like": main.get("feels_like", 0),
                    "humidity": main.get("humidity", 0),
                    "condition": weather.get("main", "").lower(),
                    "description": weather.get("description", ""),
                    "wind_speed": wind.get("speed", 0),
                    "wind_direction": wind.get("deg", 0),
                    "precipitation": closest_forecast.get("rain", {}).get("3h", 0),
                    "is_outdoor": is_outdoor,
                    "affects_game": self._weather_affects_game(main, weather, wind) if is_outdoor else False,
                }
            
            return {}
            
        except Exception as e:
            print(f"Error parsing weather data: {e}")
            return {}
    
    def _is_outdoor_stadium(self, team_name: str) -> bool:
        """Determine if stadium is outdoor based on team name"""
        team_lower = team_name.lower()
        
        # Special team name mappings (e.g., "New York Jets" -> MetLife Stadium which is outdoor)
        team_mappings = {
            "new york jets": "east rutherford",  # MetLife Stadium - OUTDOOR
            "new york giants": "east rutherford",  # MetLife Stadium - OUTDOOR
            "jets": "east rutherford",
            "giants": "east rutherford",
        }
        
        # Check team mappings first
        for team_key, stadium_city in team_mappings.items():
            if team_key in team_lower:
                # MetLife Stadium is outdoor
                return stadium_city not in self.indoor_stadiums
        
        # Check if team's stadium is in the indoor list
        for indoor_city in self.indoor_stadiums:
            if indoor_city in team_lower or team_lower in indoor_city:
                return False
        
        # Default to outdoor (most NFL stadiums are outdoor)
        return True
    
    def _weather_affects_game(self, main: Dict, weather: Dict, wind: Dict) -> bool:
        """Determine if weather significantly affects game"""
        condition = weather.get("main", "").lower()
        wind_speed = wind.get("speed", 0)
        temp = main.get("temp", 70)
        precipitation = main.get("humidity", 0)
        
        # High wind, extreme temps, or precipitation
        if wind_speed > 15:  # mph
            return True
        if temp < 20 or temp > 95:
            return True
        if condition in ["rain", "snow", "thunderstorm"]:
            return True
        
        return False
    
    def _get_basic_weather_estimate(self, team_name: str, game_time: datetime) -> Dict:
        """Fallback weather estimate when API unavailable"""
        # Check if stadium is outdoor
        is_outdoor = self._is_outdoor_stadium(team_name)
        
        # If indoor, return minimal data
        if not is_outdoor:
            return {
                "temperature": 72,  # Typical indoor temperature
                "condition": "indoor",
                "affects_game": False,
                "is_outdoor": False,
            }
        
        # Basic seasonal estimates for outdoor stadiums
        month = game_time.month
        
        # Rough seasonal estimates
        if month in [12, 1, 2]:  # Winter
            return {
                "temperature": 40,
                "condition": "cold",
                "affects_game": True,
                "is_outdoor": True,
            }
        elif month in [9, 10]:  # Fall
            return {
                "temperature": 65,
                "condition": "clear",
                "affects_game": False,
                "is_outdoor": True,
            }
        else:  # Summer/Spring
            return {
                "temperature": 75,
                "condition": "clear",
                "affects_game": False,
                "is_outdoor": True,
            }

