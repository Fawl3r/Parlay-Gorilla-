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
        
        # NFL stadium locations (lat, lon)
        self.stadium_locations = {
            "baltimore": (39.2780, -76.6227),  # M&T Bank Stadium
            "kansas city": (39.0489, -94.4839),  # Arrowhead Stadium
            "buffalo": (42.7738, -78.7869),  # Highmark Stadium
            "miami": (25.9580, -80.2389),  # Hard Rock Stadium
            "foxborough": (42.0939, -71.2642),  # Gillette Stadium
            "east rutherford": (40.8136, -74.0744),  # MetLife Stadium
            "cincinnati": (39.0950, -84.5160),  # Paycor Stadium
            "cleveland": (41.5061, -81.6996),  # FirstEnergy Stadium
            "pittsburgh": (40.4468, -80.0158),  # Acrisure Stadium
            "houston": (29.6847, -95.4107),  # NRG Stadium
            "indianapolis": (39.7601, -86.1639),  # Lucas Oil Stadium
            "jacksonville": (30.3239, -81.6373),  # TIAA Bank Field
            "nashville": (36.1665, -86.7713),  # Nissan Stadium
            "denver": (39.7439, -105.0200),  # Empower Field
            "los angeles": (34.0141, -118.2879),  # SoFi Stadium
            "las vegas": (36.0908, -115.1837),  # Allegiant Stadium
            "dallas": (32.7473, -97.0945),  # AT&T Stadium
            "new york": (40.8136, -74.0744),  # MetLife Stadium
            "philadelphia": (39.9008, -75.1675),  # Lincoln Financial Field
            "landover": (38.9076, -76.8644),  # FedExField
            "chicago": (41.8625, -87.6167),  # Soldier Field
            "detroit": (42.3400, -83.0456),  # Ford Field
            "green bay": (44.5013, -88.0622),  # Lambeau Field
            "minneapolis": (44.9740, -93.2581),  # U.S. Bank Stadium
            "atlanta": (33.7550, -84.4010),  # Mercedes-Benz Stadium
            "charlotte": (35.2258, -80.8528),  # Bank of America Stadium
            "new orleans": (29.9511, -90.0815),  # Caesars Superdome
            "tampa": (27.9756, -82.5033),  # Raymond James Stadium
            "phoenix": (33.5275, -112.2625),  # State Farm Stadium
            "inglewood": (34.0141, -118.2879),  # SoFi Stadium
            "santa clara": (37.4030, -121.9694),  # Levi's Stadium
            "seattle": (47.5952, -122.3316),  # Lumen Field
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
                    return self._parse_weather_data(data, game_time)
                else:
                    print(f"Weather API error: {response.status_code}")
                    return self._get_basic_weather_estimate(home_team, game_time)
                    
        except Exception as e:
            print(f"Error fetching weather: {e}")
            return self._get_basic_weather_estimate(home_team, game_time)
    
    def _get_stadium_coords(self, team_name: str, location: Optional[str] = None) -> Optional[tuple]:
        """Get stadium coordinates for a team"""
        team_lower = team_name.lower()
        
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
    
    def _parse_weather_data(self, data: Dict, game_time: datetime) -> Dict:
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
                
                return {
                    "temperature": main.get("temp", 0),
                    "feels_like": main.get("feels_like", 0),
                    "humidity": main.get("humidity", 0),
                    "condition": weather.get("main", "").lower(),
                    "description": weather.get("description", ""),
                    "wind_speed": wind.get("speed", 0),
                    "wind_direction": wind.get("deg", 0),
                    "precipitation": closest_forecast.get("rain", {}).get("3h", 0),
                    "is_outdoor": self._is_outdoor_stadium(closest_forecast),
                    "affects_game": self._weather_affects_game(main, weather, wind),
                }
            
            return {}
            
        except Exception as e:
            print(f"Error parsing weather data: {e}")
            return {}
    
    def _is_outdoor_stadium(self, forecast: Dict) -> bool:
        """Determine if stadium is outdoor (simplified - most NFL stadiums are outdoor)"""
        # Most NFL stadiums are outdoor, except domes
        # This is a simplified check - could be enhanced with stadium database
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
        # Basic seasonal estimates
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

