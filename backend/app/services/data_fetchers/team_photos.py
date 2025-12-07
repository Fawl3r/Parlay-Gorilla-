"""Service for fetching real team action photos from sports photo APIs"""

import httpx
from typing import Optional, Dict, List
from app.core.config import settings
import hashlib
import json
from datetime import datetime, timedelta


class TeamPhotoFetcher:
    """
    Fetches real in-game action photos for teams.
    
    Prioritizes Getty Images/Imagn API (same as Covers.com uses) for best quality.
    Falls back to Pexels, Unsplash, and free sources.
    
    Uses Imagn-style search queries (e.g., "miami dolphins v new york jets")
    for better team-specific results.
    
    For production, integrate with:
    - Getty Images/Imagn API (BEST - same as Covers.com, requires license)
    - Pexels API (free tier, good quality)
    - Unsplash API (free tier)
    - Or store curated photos in CDN
    """
    
    def __init__(self):
        self.timeout = 10.0
        self.unsplash_access_key = getattr(settings, 'unsplash_access_key', None)
        self.unsplash_base_url = "https://api.unsplash.com"
        self.pexels_api_key = getattr(settings, 'pexels_api_key', None)
        self.pexels_base_url = "https://api.pexels.com/v1"
        self.getty_images_api_key = getattr(settings, 'getty_images_api_key', None)
        self.getty_images_api_secret = getattr(settings, 'getty_images_api_secret', None)
        self.getty_base_url = "https://api.gettyimages.com/v3"
        self._getty_access_token = None  # Cache the access token
        
        # In-memory cache for stadium photos (key: cache_key, value: (photos, expiry_time))
        self._stadium_photo_cache: Dict[str, tuple] = {}
        self._cache_ttl_hours = 24 * 7  # Cache for 7 days (stadium photos don't change often)
        
        # Stadium names mapped to team names (for fetching stadium photos)
        self.stadium_mapping = {
            # NFL
            'miami dolphins': 'hard rock stadium',
            'new york jets': 'metlife stadium',
            'buffalo bills': 'highmark stadium',
            'new england patriots': 'gillette stadium',
            'baltimore ravens': 'm&t bank stadium',
            'cincinnati bengals': 'paycor stadium',
            'cleveland browns': 'firstenergy stadium',
            'pittsburgh steelers': 'acrisure stadium',
            'houston texans': 'nrg stadium',
            'indianapolis colts': 'lucas oil stadium',
            'jacksonville jaguars': 'tiaa bank field',
            'tennessee titans': 'nissan stadium',
            'denver broncos': 'empower field',
            'kansas city chiefs': 'arrowhead stadium',
            'las vegas raiders': 'allegiant stadium',
            'los angeles chargers': 'sofi stadium',
            'dallas cowboys': 'at&t stadium',
            'new york giants': 'metlife stadium',
            'philadelphia eagles': 'lincoln financial field',
            'washington commanders': 'fedexfield',
            'chicago bears': 'soldier field',
            'detroit lions': 'ford field',
            'green bay packers': 'lambeau field',
            'minnesota vikings': 'u.s. bank stadium',
            'atlanta falcons': 'mercedes-benz stadium',
            'carolina panthers': 'bank of america stadium',
            'new orleans saints': 'caesars superdome',
            'tampa bay buccaneers': 'raymond james stadium',
            'arizona cardinals': 'state farm stadium',
            'los angeles rams': 'sofi stadium',
            'san francisco 49ers': "levi's stadium",
            'seattle seahawks': 'lumen field',
            # NBA
            'miami heat': 'ftx arena',
            'boston celtics': 'td garden',
            'los angeles lakers': 'crypto.com arena',
            'golden state warriors': 'chase center',
            # NHL
            'boston bruins': 'td garden',
            'chicago blackhawks': 'united center',
            # MLB
            'boston red sox': 'fenway park',
            'chicago cubs': 'wrigley field',
            'new york yankees': 'yankee stadium',
        }
        
        # ESPN team abbreviations mapping
        self.team_abbreviations = {
            # NFL
            'miami dolphins': 'mia', 'new york jets': 'nyj', 'buffalo bills': 'buf',
            'new england patriots': 'ne', 'baltimore ravens': 'bal', 'cincinnati bengals': 'cin',
            'cleveland browns': 'cle', 'pittsburgh steelers': 'pit', 'houston texans': 'hou',
            'indianapolis colts': 'ind', 'jacksonville jaguars': 'jax', 'tennessee titans': 'ten',
            'denver broncos': 'den', 'kansas city chiefs': 'kc', 'las vegas raiders': 'lv',
            'los angeles chargers': 'lac', 'dallas cowboys': 'dal', 'new york giants': 'nyg',
            'philadelphia eagles': 'phi', 'washington commanders': 'wsh', 'chicago bears': 'chi',
            'detroit lions': 'det', 'green bay packers': 'gb', 'minnesota vikings': 'min',
            'atlanta falcons': 'atl', 'carolina panthers': 'car', 'new orleans saints': 'no',
            'tampa bay buccaneers': 'tb', 'arizona cardinals': 'ari', 'los angeles rams': 'lar',
            'san francisco 49ers': 'sf', 'seattle seahawks': 'sea',
            # NBA
            'atlanta hawks': 'atl', 'boston celtics': 'bos', 'brooklyn nets': 'bkn',
            'charlotte hornets': 'cha', 'chicago bulls': 'chi', 'cleveland cavaliers': 'cle',
            'dallas mavericks': 'dal', 'denver nuggets': 'den', 'detroit pistons': 'det',
            'golden state warriors': 'gs', 'houston rockets': 'hou', 'indiana pacers': 'ind',
            'los angeles clippers': 'lac', 'los angeles lakers': 'lal', 'memphis grizzlies': 'mem',
            'miami heat': 'mia', 'milwaukee bucks': 'mil', 'minnesota timberwolves': 'min',
            'new orleans pelicans': 'no', 'new york knicks': 'ny', 'oklahoma city thunder': 'okc',
            'orlando magic': 'orl', 'philadelphia 76ers': 'phi', 'phoenix suns': 'phx',
            'portland trail blazers': 'por', 'sacramento kings': 'sac', 'san antonio spurs': 'sa',
            'toronto raptors': 'tor', 'utah jazz': 'uth', 'washington wizards': 'wsh',
        }
    
    async def get_team_action_photo(
        self,
        team_name: str,
        league: str,
        opponent: Optional[str] = None
    ) -> List[str]:
        """
        Get multiple photos for the matchup - prioritizes home team's stadium photos.
        
        NOTE: Team-specific action photos require licensing (Getty Images/Imagn).
        Until a license is obtained, we use stadium photos which are publicly available.
        
        Args:
            team_name: Name of the home team
            league: League (NFL, NBA, NHL, MLB)
            opponent: Optional opponent team name (not used for stadium photos)
            
        Returns:
            List of photo URLs (stadium photos for carousel display)
        """
        # Check cache first
        cache_key = self._get_cache_key(team_name, league)
        cached_photos = self._get_cached_photos(cache_key)
        if cached_photos:
            return cached_photos
        
        # PRIMARY: Get multiple stadium photos for home team (no licensing needed!)
        stadium_photos = await self._get_stadium_photos(team_name, league)
        if stadium_photos and len(stadium_photos) > 0:
            # Cache the results
            self._cache_photos(cache_key, stadium_photos)
            return stadium_photos
        
        # Fallback: Use high-quality free sports photos from known sources
        free_photo_url = self._get_free_sports_photo(team_name, league)
        if free_photo_url:
            photos = [free_photo_url]
            self._cache_photos(cache_key, photos)
            return photos
        
        # Fallback: try curated photos
        curated_url = self._get_curated_photo_url(team_name, league)
        if curated_url:
            photos = [curated_url]
            self._cache_photos(cache_key, photos)
            return photos
        
        return []
    
    def _get_cache_key(self, team_name: str, league: str) -> str:
        """Generate cache key for stadium photos"""
        key_string = f"stadium_photos:{league.lower()}:{team_name.lower().strip()}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cached_photos(self, cache_key: str) -> Optional[List[str]]:
        """Get cached photos if they exist and haven't expired"""
        if cache_key not in self._stadium_photo_cache:
            return None
        
        photos, expiry_time = self._stadium_photo_cache[cache_key]
        
        # Check if cache has expired
        if datetime.now() > expiry_time:
            del self._stadium_photo_cache[cache_key]
            return None
        
        return photos
    
    def _cache_photos(self, cache_key: str, photos: List[str]):
        """Cache photos with expiry time"""
        expiry_time = datetime.now() + timedelta(hours=self._cache_ttl_hours)
        self._stadium_photo_cache[cache_key] = (photos, expiry_time)
    
    async def _get_stadium_photos(
        self,
        team_name: str,
        league: str
    ) -> List[str]:
        """
        Get multiple photos of the home team's stadium for carousel display.
        Stadium photos are publicly available and don't require licensing.
        
        Returns:
            List of stadium photo URLs (typically 3-8 photos)
        """
        try:
            team_lower = team_name.lower().strip()
            stadium_name = self.stadium_mapping.get(team_lower)
            
            if not stadium_name:
                return []
            
            league_lower = league.lower()
            all_photos = []
            
            # Try Pexels first for stadium photos (get multiple)
            if self.pexels_api_key:
                pexels_photos = await self._search_pexels_stadium(stadium_name, league_lower, count=8)
                if pexels_photos:
                    all_photos.extend(pexels_photos)
            
            # Try Unsplash for stadium photos (get multiple)
            if self.unsplash_access_key:
                unsplash_photos = await self._search_unsplash_stadium(stadium_name, league_lower, count=8)
                if unsplash_photos:
                    all_photos.extend(unsplash_photos)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_photos = []
            for photo in all_photos:
                if photo not in seen:
                    seen.add(photo)
                    unique_photos.append(photo)
            
            # If we have photos, return them (limit to 10 for carousel)
            if unique_photos:
                return unique_photos[:10]
            
            # Fallback: Use known good stadium photo URLs from Pexels
            curated_photo = self._get_curated_stadium_photo(stadium_name, league_lower)
            if curated_photo:
                return [curated_photo]
            
            return []
            
        except Exception as e:
            print(f"Error fetching stadium photos for {team_name}: {e}")
            return []
    
    async def _search_pexels_stadium(
        self,
        stadium_name: str,
        league: str,
        count: int = 8
    ) -> List[str]:
        """Search Pexels for multiple stadium photos"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {
                    "Authorization": self.pexels_api_key
                }
                
                all_photos = []
                
                # Try multiple search queries to get variety
                queries = [
                    f"{stadium_name} stadium",
                    f"{stadium_name}",
                    f"{stadium_name} exterior",
                    f"{stadium_name} architecture",
                    f"{stadium_name} night",
                ]
                
                for query in queries:
                    try:
                        url = f"{self.pexels_base_url}/search"
                        params = {
                            "query": query,
                            "per_page": min(count, 15),  # Get more results per query
                            "orientation": "landscape",
                        }
                        
                        response = await client.get(url, params=params, headers=headers)
                        
                        if response.status_code == 200:
                            data = response.json()
                            photos = data.get("photos", [])
                            for photo in photos:
                                large_url = photo.get("src", {}).get("large")
                                if large_url:
                                    # Format URL for hero image dimensions (1400x560)
                                    formatted_url = large_url.replace("&h=650&w=940", "&h=560&w=1400").replace("?auto=compress", "?auto=compress&fit=crop")
                                    all_photos.append(formatted_url)
                                elif photo.get("src", {}).get("original"):
                                    all_photos.append(photo.get("src", {}).get("original"))
                                
                                # Stop if we have enough photos
                                if len(all_photos) >= count:
                                    break
                        
                        # Stop if we have enough photos
                        if len(all_photos) >= count:
                            break
                            
                    except Exception as e:
                        print(f"Error with Pexels stadium query '{query}': {e}")
                        continue
                
                return all_photos[:count]
                
        except Exception as e:
            print(f"Error searching Pexels for stadium: {e}")
            return []
    
    async def _search_unsplash_stadium(
        self,
        stadium_name: str,
        league: str,
        count: int = 8
    ) -> List[str]:
        """Search Unsplash for multiple stadium photos"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.unsplash_base_url}/search/photos"
                headers = {
                    "Authorization": f"Client-ID {self.unsplash_access_key}"
                }
                
                all_photos = []
                
                queries = [
                    f"{stadium_name} stadium",
                    f"{stadium_name}",
                    f"{stadium_name} exterior",
                ]
                
                for query in queries:
                    try:
                        params = {
                            "query": query,
                            "per_page": min(count, 10),
                            "orientation": "landscape",
                        }
                        
                        response = await client.get(url, params=params, headers=headers)
                        
                        if response.status_code == 200:
                            data = response.json()
                            results = data.get("results", [])
                            for photo in results:
                                photo_url = photo.get("urls", {}).get("regular")
                                if photo_url:
                                    all_photos.append(photo_url)
                                
                                # Stop if we have enough photos
                                if len(all_photos) >= count:
                                    break
                        
                        # Stop if we have enough photos
                        if len(all_photos) >= count:
                            break
                            
                    except Exception as e:
                        print(f"Error with Unsplash stadium query '{query}': {e}")
                        continue
                
                return all_photos[:count]
                
        except Exception as e:
            print(f"Error searching Unsplash for stadium: {e}")
            return []
    
    def _get_curated_stadium_photo(
        self,
        stadium_name: str,
        league: str
    ) -> Optional[str]:
        """
        Return curated stadium photo URLs from known good sources.
        These are public domain or free-use stadium photos.
        """
        # Map of known good stadium photo URLs (can be expanded)
        curated_stadiums = {
            'lambeau field': 'https://images.pexels.com/photos/207247/pexels-photo-207247.jpeg?auto=compress&cs=tinysrgb&w=1400&h=560&fit=crop',
            'soldier field': 'https://images.pexels.com/photos/46798/the-ball-stadion-football-the-pitch-46798.jpeg?auto=compress&cs=tinysrgb&w=1400&h=560&fit=crop',
            'arrowhead stadium': 'https://images.pexels.com/photos/1884574/pexels-photo-1884574.jpeg?auto=compress&cs=tinysrgb&w=1400&h=560&fit=crop',
            # Add more as needed
        }
        
        stadium_lower = stadium_name.lower()
        return curated_stadiums.get(stadium_lower)
    
    def _get_free_sports_photo(self, team_name: str, league: str) -> Optional[str]:
        """
        Get free high-quality sports photos from public sources.
        Uses direct URLs to known good sports photography.
        """
        try:
            league_lower = league.lower()
            team_lower = team_name.lower()
            
            # Use Pexels curated sports photos (no API key needed for direct URLs)
            # These are high-quality sports action photos
            sport_photos = {
                'nfl': [
                    'https://images.pexels.com/photos/3148452/pexels-photo-3148452.jpeg?auto=compress&cs=tinysrgb&w=1400&h=560&fit=crop',
                    'https://images.pexels.com/photos/1884574/pexels-photo-1884574.jpeg?auto=compress&cs=tinysrgb&w=1400&h=560&fit=crop',
                    'https://images.pexels.com/photos/46798/the-ball-stadion-football-the-pitch-46798.jpeg?auto=compress&cs=tinysrgb&w=1400&h=560&fit=crop',
                ],
                'nba': [
                    'https://images.pexels.com/photos/1752757/pexels-photo-1752757.jpeg?auto=compress&cs=tinysrgb&w=1400&h=560&fit=crop',
                    'https://images.pexels.com/photos/358042/pexels-photo-358042.jpeg?auto=compress&cs=tinysrgb&w=1400&h=560&fit=crop',
                ],
                'nhl': [
                    'https://images.pexels.com/photos/163444/sport-hockey-ice-hockey-puck-163444.jpeg?auto=compress&cs=tinysrgb&w=1400&h=560&fit=crop',
                ],
                'mlb': [
                    'https://images.pexels.com/photos/159711/books-bookstore-book-reading-159711.jpeg?auto=compress&cs=tinysrgb&w=1400&h=560&fit=crop',
                ],
            }
            
            # Get a photo based on team name hash for consistency
            photos = sport_photos.get(league_lower, [])
            if photos:
                # Use team name to consistently select same photo per team
                team_hash = hash(team_lower) % len(photos)
                return photos[team_hash]
            
        except Exception as e:
            print(f"Error getting free sports photo: {e}")
            return None
        
        return None
    
    def _get_espn_action_photo(self, team_name: str, league: str) -> Optional[str]:
        """
        Get ESPN team action photo URL from their public CDN.
        ESPN stores team header images and action photos publicly.
        """
        try:
            team_lower = team_name.lower()
            league_lower = league.lower()
            team_abbr = self.team_abbreviations.get(team_lower)
            
            if not team_abbr:
                return None
            
            # ESPN team header images (these are actual game action photos)
            # Format: https://a.espncdn.com/combiner/i?img=/i/teamlogos/{league}/500-dark/{abbr}.png&w=1400&h=560&scale=crop&cquality=80
            # These are high-quality team action photos used on ESPN team pages
            if league_lower == 'nfl':
                return f"https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500-dark/{team_abbr}.png&w=1400&h=560&scale=crop&cquality=80"
            elif league_lower == 'nba':
                return f"https://a.espncdn.com/combiner/i?img=/i/teamlogos/nba/500-dark/{team_abbr}.png&w=1400&h=560&scale=crop&cquality=80"
            elif league_lower == 'nhl':
                return f"https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500-dark/{team_abbr}.png&w=1400&h=560&scale=crop&cquality=80"
            elif league_lower == 'mlb':
                return f"https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500-dark/{team_abbr}.png&w=1400&h=560&scale=crop&cquality=80"
            
        except Exception as e:
            print(f"Error constructing ESPN URL for {team_name}: {e}")
            return None
    
    async def _get_getty_access_token(self) -> Optional[str]:
        """
        Get OAuth2 access token from Getty Images API.
        Uses Client Credentials flow as per Getty Images documentation.
        """
        if not self.getty_images_api_key or not self.getty_images_api_secret:
            return None
        
        # Return cached token if available
        if self._getty_access_token:
            return self._getty_access_token
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = "https://api.gettyimages.com/oauth2/token"
                data = {
                    "grant_type": "client_credentials",
                    "client_id": self.getty_images_api_key,
                    "client_secret": self.getty_images_api_secret,
                }
                headers = {
                    "Content-Type": "application/x-www-form-urlencoded"
                }
                
                response = await client.post(url, data=data, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    self._getty_access_token = result.get("access_token")
                    return self._getty_access_token
                else:
                    print(f"Getty Images token error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            print(f"Error getting Getty Images access token: {e}")
            return None
    
    async def _get_getty_photo(
        self,
        team_name: str,
        league: str,
        opponent: Optional[str] = None
    ) -> Optional[str]:
        """
        Get team-specific action photos from Getty Images/Imagn API.
        This is the same service Covers.com uses for their photos.
        
        Follows Getty Images API workflow:
        1. Get access token (OAuth2)
        2. Search for images
        3. Get download URI from largest_downloads
        """
        if not self.getty_images_api_key or not self.getty_images_api_secret:
            return None
        
        # Get access token first
        access_token = await self._get_getty_access_token()
        if not access_token:
            return None
            
        try:
            # Build Imagn-style search query (like "new york jets v miami dolphins")
            if opponent:
                # Matchup-specific search: "team1 v team2"
                query = f"{team_name} v {opponent}"
            else:
                # Team-specific search
                query = f"{team_name} {league}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Step 1: Search for images
                search_url = f"{self.getty_base_url}/search/images"
                params = {
                    "phrase": query,
                    "page_size": 1,
                    "sort_order": "best_match",
                    "graphical_styles": "photography",  # Only photos, not illustrations
                    "fields": "id,largest_downloads,display_sizes",  # Request download info
                }
                headers = {
                    "Api-Key": self.getty_images_api_key,
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                }
                
                response = await client.get(search_url, params=params, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    images = data.get("images", [])
                    if images:
                        image = images[0]
                        image_id = image.get("id")
                        
                        # Step 2: Get download URI from largest_downloads
                        largest_downloads = image.get("largest_downloads", [])
                        if largest_downloads:
                            download_info = largest_downloads[0]
                            product_type = download_info.get("product_type")
                            download_uri = download_info.get("uri")
                            
                            # Step 3: Get actual image download URL
                            if download_uri and product_type:
                                download_response = await client.post(
                                    f"{download_uri}?auto_download=false&product_type={product_type}",
                                    headers={
                                        "Api-Key": self.getty_images_api_key,
                                        "Authorization": f"Bearer {access_token}",
                                    }
                                )
                                
                                if download_response.status_code == 200:
                                    download_data = download_response.json()
                                    return download_data.get("uri")
                        
                        # Fallback: Use display_sizes if available
                        display_sizes = image.get("display_sizes", [])
                        if display_sizes:
                            # Get the largest available preview size
                            largest = max(display_sizes, key=lambda x: x.get("width", 0))
                            return largest.get("uri")
                        
                elif response.status_code == 401:
                    # Token expired, clear cache and retry once
                    self._getty_access_token = None
                    access_token = await self._get_getty_access_token()
                    if access_token:
                        # Retry the search
                        return await self._get_getty_photo(team_name, league, opponent)
                        
        except Exception as e:
            print(f"Error fetching Getty/Imagn photo for {team_name}: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        return None
    
    async def _get_pexels_photo(
        self,
        team_name: str,
        league: str,
        opponent: Optional[str] = None
    ) -> Optional[str]:
        """Search Pexels for team-specific sports photos (better quality than Unsplash)"""
        if not self.pexels_api_key:
            return None
            
        try:
            league_lower = league.lower()
            
            # Sport-specific search terms
            sport_terms = {
                'nfl': 'american football',
                'nba': 'basketball',
                'nhl': 'ice hockey',
                'mlb': 'baseball',
            }
            sport_term = sport_terms.get(league_lower, 'sports')
            
            # Build matchup-specific queries with team names AND strong sports context
            # Use team names to get matchup-relevant photos, but add sports keywords to filter
            if opponent:
                # Matchup-specific: Use both team names with sports context
                # This mimics Imagn search: "miami dolphins v new york jets"
                team1_clean = team_name.lower().strip()
                team2_clean = opponent.lower().strip()
                
                if league_lower == 'nfl':
                    # Try multiple query formats to find team-specific photos
                    search_queries = [
                        f"{team1_clean} {team2_clean} football",  # Both teams + sport
                        f"{team1_clean} vs {team2_clean} football",  # With "vs"
                        f"{team1_clean} v {team2_clean} football",  # With "v" (Imagn style)
                        f"{team1_clean} {team2_clean} nfl game",  # With league
                        f"{team1_clean} football {sport_term}",  # Team 1 + sport
                        f"{team2_clean} football {sport_term}",  # Team 2 + sport
                        f"{sport_term} game action",  # Generic fallback
                    ]
                else:
                    search_queries = [
                        f"{team1_clean} {team2_clean} {sport_term}",
                        f"{team1_clean} vs {team2_clean} {sport_term}",
                        f"{team1_clean} {sport_term} game",
                        f"{team2_clean} {sport_term} game",
                        f"{sport_term} game action",
                    ]
            else:
                # Single team searches with sports context
                team_clean = team_name.lower().strip()
                if league_lower == 'nfl':
                    search_queries = [
                        f"{team_clean} football game",
                        f"{team_clean} nfl {sport_term}",
                        f"{team_clean} football player",
                        f"{sport_term} game action",
                    ]
                else:
                    search_queries = [
                        f"{team_clean} {sport_term} game",
                        f"{team_clean} {sport_term}",
                        f"{sport_term} game action",
                    ]
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {
                    "Authorization": self.pexels_api_key  # Pexels uses API key directly as Authorization header
                }
                
                for query in search_queries:
                    try:
                        url = f"{self.pexels_base_url}/search"
                        params = {
                            "query": query,
                            "per_page": 10,  # Get more results to filter through
                            "orientation": "landscape",
                        }
                        
                        response = await client.get(url, params=params, headers=headers)
                        
                        if response.status_code == 200:
                            data = response.json()
                            photos = data.get("photos", [])
                            if photos:
                                # Filter photos to ensure they're sports-related
                                # Use strict sports keywords to avoid non-sports images
                                if league_lower == 'nfl':
                                    required_keywords = ['football', 'nfl', 'player', 'game', 'stadium', 'field', 'athlete', 'sport', 'team']
                                    exclude_keywords = ['building', 'station', 'train', 'architecture', 'hall', 'terminal', 'grand central', 'wreath', 'holiday']
                                else:
                                    required_keywords = ['sport', 'game', 'player', 'athlete', 'field', 'court', 'stadium', 'team']
                                    exclude_keywords = ['building', 'station', 'train', 'architecture']
                                
                                # Also check if photo URL or ID suggests it's sports-related
                                for photo in photos:
                                    alt_text = photo.get("alt", "").lower()
                                    photo_url = photo.get("url", "").lower()
                                    
                                    # Must contain at least one sports keyword
                                    has_sports_keyword = any(keyword in alt_text for keyword in required_keywords)
                                    
                                    # Must NOT contain excluded keywords (buildings, etc.)
                                    has_excluded = any(keyword in alt_text for keyword in exclude_keywords)
                                    
                                    # Check URL for sports indicators
                                    url_is_sports = any(keyword in photo_url for keyword in ['sport', 'football', 'basketball', 'hockey', 'baseball'])
                                    
                                    if (has_sports_keyword or url_is_sports) and not has_excluded:
                                        # This is a valid sports photo
                                        large_url = photo.get("src", {}).get("large")
                                        if large_url:
                                            # Format URL for hero image dimensions (1400x560)
                                            return large_url.replace("&h=650&w=940", "&h=560&w=1400").replace("?auto=compress", "?auto=compress&fit=crop")
                                        return photo.get("src", {}).get("original")
                                
                                # If no photos passed strict filter, try less strict
                                # At minimum, must have 'sport' or 'game' in alt text AND not be excluded
                                for photo in photos:
                                    alt_text = photo.get("alt", "").lower()
                                    has_excluded = any(keyword in alt_text for keyword in exclude_keywords)
                                    
                                    if not has_excluded and ('sport' in alt_text or 'game' in alt_text or 'player' in alt_text or 'football' in alt_text):
                                        large_url = photo.get("src", {}).get("large")
                                        if large_url:
                                            return large_url.replace("&h=650&w=940", "&h=560&w=1400").replace("?auto=compress", "?auto=compress&fit=crop")
                                        return photo.get("src", {}).get("original")
                                
                                # Last resort: skip this query and try next one
                                continue
                    except Exception as e:
                        print(f"Error with Pexels query '{query}': {e}")
                        continue
                
                return None
                        
        except Exception as e:
            print(f"Error fetching Pexels photo for {team_name}: {e}")
            return None
    
    async def _verify_image_exists(self, url: str) -> bool:
        """Verify that an image URL actually exists and is accessible"""
        try:
            async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
                response = await client.head(url)
                return response.status_code == 200
        except:
            return False
    
    async def _get_unsplash_photo(
        self,
        team_name: str,
        league: str,
        opponent: Optional[str] = None
    ) -> Optional[str]:
        """Search Unsplash for team-specific sports photos"""
        if not self.unsplash_access_key:
            print("Unsplash API key not configured, skipping photo fetch")
            return None
            
        try:
            # Build search query with team name and sport
            league_lower = league.lower()
            
            # Sport-specific search terms
            sport_terms = {
                'nfl': 'american football',
                'nba': 'basketball',
                'nhl': 'ice hockey',
                'mlb': 'baseball',
            }
            sport_term = sport_terms.get(league_lower, 'sports')
            
            # Try Imagn-style search queries for better team-specific results
            if opponent:
                # Matchup-specific: "team1 v team2" (like Imagn search)
                search_queries = [
                    f"{team_name} v {opponent} {sport_term}",
                    f"{team_name} vs {opponent} {sport_term}",
                    f"{team_name} {sport_term} game",
                ]
            else:
                # Team-specific searches
                search_queries = [
                    f"{team_name} {sport_term} game",  # Full team name
                    f"{team_name} {sport_term} action",  # With action keyword
                    f"{sport_term} game action",  # Generic sport action
                ]
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {
                    "Authorization": f"Client-ID {self.unsplash_access_key}"
                }
                
                # Try each query until we get results
                for query in search_queries:
                    try:
                        url = f"{self.unsplash_base_url}/search/photos"
                        params = {
                            "query": query,
                            "per_page": 5,  # Get a few results to choose from
                            "orientation": "landscape",
                            "content_filter": "high",
                        }
                        
                        response = await client.get(url, params=params, headers=headers)
                        
                        if response.status_code == 200:
                            data = response.json()
                            results = data.get("results", [])
                            if results:
                                # Get the first (best) result
                                photo = results[0]
                                # Return regular size (1080px width, good for hero images)
                                return photo.get("urls", {}).get("regular")
                    except Exception as e:
                        print(f"Error with query '{query}': {e}")
                        continue
                
                # If all queries fail, return None
                return None
                        
        except Exception as e:
            print(f"Error fetching Unsplash photo for {team_name}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    
    def _get_curated_photo_url(self, team_name: str, league: str) -> Optional[str]:
        """
        Get curated photo URL from CDN or local storage.
        
        In production, store curated team action photos in:
        - AWS S3 / CloudFront
        - Cloudinary
        - Your own CDN
        
        Format: /images/teams/{league}/{team_slug}/action-{photo_id}.jpg
        """
        # TODO: Implement curated photo lookup
        return None

