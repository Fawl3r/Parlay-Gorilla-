"""
SportsRadar MLB API Client

Fetches MLB-specific data:
- Team statistics (batting, pitching)
- Starting pitcher matchups
- Bullpen strength
- Game schedules and results
- Injury reports
"""

from typing import Dict, Optional, List
import logging
from functools import lru_cache

from app.services.data_fetchers.sportsradar_base import SportsRadarBase

logger = logging.getLogger(__name__)


class SportsRadarMLB(SportsRadarBase):
    """
    SportsRadar MLB API client.
    
    Provides MLB-specific team stats including:
    - Batting average, OPS, runs
    - Team ERA, WHIP
    - Bullpen strength metrics
    - Park factors
    """
    
    def __init__(self):
        super().__init__(sport_code="mlb")
    
    @property
    def base_url(self) -> str:
        return "https://api.sportradar.us/mlb/trial/v7/en"
    
    # MLB team mapping: name/city -> SportsRadar team ID
    TEAM_MAP = {
        # AL East
        "orioles": "75729d34-bca7-4a0f-b3df-6f26c6ad3719",
        "baltimore": "75729d34-bca7-4a0f-b3df-6f26c6ad3719",
        "baltimore orioles": "75729d34-bca7-4a0f-b3df-6f26c6ad3719",
        "red sox": "93941372-eb4c-4c40-aced-fe3267174393",
        "boston": "93941372-eb4c-4c40-aced-fe3267174393",
        "boston red sox": "93941372-eb4c-4c40-aced-fe3267174393",
        "yankees": "a09ec676-f887-43dc-bbb3-cf4bbaee9a18",
        "new york yankees": "a09ec676-f887-43dc-bbb3-cf4bbaee9a18",
        "rays": "bdc11650-6f74-49c4-875e-778aeb7632d9",
        "tampa bay": "bdc11650-6f74-49c4-875e-778aeb7632d9",
        "tampa bay rays": "bdc11650-6f74-49c4-875e-778aeb7632d9",
        "blue jays": "1d678440-b4b1-4954-9b39-70afb3ebbcfa",
        "jays": "1d678440-b4b1-4954-9b39-70afb3ebbcfa",
        "toronto": "1d678440-b4b1-4954-9b39-70afb3ebbcfa",
        "toronto blue jays": "1d678440-b4b1-4954-9b39-70afb3ebbcfa",
        
        # AL Central
        "white sox": "47f490cd-2f58-4ef7-9dfd-2ad6ba6c1ae8",
        "chicago white sox": "47f490cd-2f58-4ef7-9dfd-2ad6ba6c1ae8",
        "guardians": "80715d0d-0d2a-450f-a970-1b9a3b18c7e7",
        "cleveland": "80715d0d-0d2a-450f-a970-1b9a3b18c7e7",
        "cleveland guardians": "80715d0d-0d2a-450f-a970-1b9a3b18c7e7",
        "tigers": "575c19b7-4052-41c2-9f0a-1c5813d02f99",
        "detroit": "575c19b7-4052-41c2-9f0a-1c5813d02f99",
        "detroit tigers": "575c19b7-4052-41c2-9f0a-1c5813d02f99",
        "royals": "833a51a9-0d84-410f-bd77-da08c3e5e26e",
        "kansas city": "833a51a9-0d84-410f-bd77-da08c3e5e26e",
        "kansas city royals": "833a51a9-0d84-410f-bd77-da08c3e5e26e",
        "twins": "aa34e0ed-f342-4ec6-b774-c79b47b60e2d",
        "minnesota": "aa34e0ed-f342-4ec6-b774-c79b47b60e2d",
        "minnesota twins": "aa34e0ed-f342-4ec6-b774-c79b47b60e2d",
        
        # AL West
        "astros": "eb21dadd-8f10-4095-8571-3c5273913103",
        "houston": "eb21dadd-8f10-4095-8571-3c5273913103",
        "houston astros": "eb21dadd-8f10-4095-8571-3c5273913103",
        "angels": "4f735188-37c8-473d-ae32-1f7e34ccf892",
        "los angeles angels": "4f735188-37c8-473d-ae32-1f7e34ccf892",
        "la angels": "4f735188-37c8-473d-ae32-1f7e34ccf892",
        "athletics": "27a59d3b-ff7c-48ea-b016-4798f560f5e1",
        "a's": "27a59d3b-ff7c-48ea-b016-4798f560f5e1",
        "oakland": "27a59d3b-ff7c-48ea-b016-4798f560f5e1",
        "oakland athletics": "27a59d3b-ff7c-48ea-b016-4798f560f5e1",
        "mariners": "43a39081-52b4-4f93-ad29-da7f329ea960",
        "seattle": "43a39081-52b4-4f93-ad29-da7f329ea960",
        "seattle mariners": "43a39081-52b4-4f93-ad29-da7f329ea960",
        "rangers": "d99f919b-1534-4516-8e8a-9cd106c6d8cd",
        "texas": "d99f919b-1534-4516-8e8a-9cd106c6d8cd",
        "texas rangers": "d99f919b-1534-4516-8e8a-9cd106c6d8cd",
        
        # NL East
        "braves": "12079497-e414-450a-8bf2-29f91de646bf",
        "atlanta": "12079497-e414-450a-8bf2-29f91de646bf",
        "atlanta braves": "12079497-e414-450a-8bf2-29f91de646bf",
        "marlins": "03556285-bdbb-4576-a06d-42f71f46ddc5",
        "miami": "03556285-bdbb-4576-a06d-42f71f46ddc5",
        "miami marlins": "03556285-bdbb-4576-a06d-42f71f46ddc5",
        "mets": "f246a5e5-afdb-479c-9aaa-c68beeda7af6",
        "new york mets": "f246a5e5-afdb-479c-9aaa-c68beeda7af6",
        "phillies": "2142e1ba-3b40-445c-b8bb-f1f8b1054220",
        "philadelphia": "2142e1ba-3b40-445c-b8bb-f1f8b1054220",
        "philadelphia phillies": "2142e1ba-3b40-445c-b8bb-f1f8b1054220",
        "nationals": "d89bed32-3aee-4407-99e3-4103f1b0b527",
        "washington": "d89bed32-3aee-4407-99e3-4103f1b0b527",
        "washington nationals": "d89bed32-3aee-4407-99e3-4103f1b0b527",
        
        # NL Central
        "cubs": "55714da8-fcaf-4574-8443-59bfb511a524",
        "chicago cubs": "55714da8-fcaf-4574-8443-59bfb511a524",
        "reds": "c874a065-c115-4e7d-b0f0-235584fb0e6f",
        "cincinnati": "c874a065-c115-4e7d-b0f0-235584fb0e6f",
        "cincinnati reds": "c874a065-c115-4e7d-b0f0-235584fb0e6f",
        "brewers": "dcfd5266-00ce-442c-bc09-264cd20cf455",
        "milwaukee": "dcfd5266-00ce-442c-bc09-264cd20cf455",
        "milwaukee brewers": "dcfd5266-00ce-442c-bc09-264cd20cf455",
        "pirates": "481dfe7e-5dab-46ab-a49f-9dcc2b6e2cfd",
        "pittsburgh": "481dfe7e-5dab-46ab-a49f-9dcc2b6e2cfd",
        "pittsburgh pirates": "481dfe7e-5dab-46ab-a49f-9dcc2b6e2cfd",
        "cardinals": "44671792-dc02-4fdd-a5ad-f5f17edaa9d7",
        "st louis": "44671792-dc02-4fdd-a5ad-f5f17edaa9d7",
        "st. louis": "44671792-dc02-4fdd-a5ad-f5f17edaa9d7",
        "st. louis cardinals": "44671792-dc02-4fdd-a5ad-f5f17edaa9d7",
        
        # NL West
        "diamondbacks": "25507be1-6a68-4267-bd82-e097d94b359b",
        "dbacks": "25507be1-6a68-4267-bd82-e097d94b359b",
        "arizona": "25507be1-6a68-4267-bd82-e097d94b359b",
        "arizona diamondbacks": "25507be1-6a68-4267-bd82-e097d94b359b",
        "rockies": "29dd9a87-5bcc-4774-80c3-7f50d985068b",
        "colorado": "29dd9a87-5bcc-4774-80c3-7f50d985068b",
        "colorado rockies": "29dd9a87-5bcc-4774-80c3-7f50d985068b",
        "dodgers": "ef64da7f-cfaf-4300-87b0-9313386b977c",
        "los angeles dodgers": "ef64da7f-cfaf-4300-87b0-9313386b977c",
        "la dodgers": "ef64da7f-cfaf-4300-87b0-9313386b977c",
        "padres": "d52d5339-cbdd-43f3-9dfa-a42fd588b9a3",
        "san diego": "d52d5339-cbdd-43f3-9dfa-a42fd588b9a3",
        "san diego padres": "d52d5339-cbdd-43f3-9dfa-a42fd588b9a3",
        "giants": "a7723160-10b7-4f5a-8b4d-c0b8d6b4d710",
        "san francisco": "a7723160-10b7-4f5a-8b4d-c0b8d6b4d710",
        "san francisco giants": "a7723160-10b7-4f5a-8b4d-c0b8d6b4d710",
    }
    
    # MLB position importance weights (starting pitcher is most important per game)
    POSITION_WEIGHTS = {
        "SP": 0.5,    # Starting pitcher (huge per-game impact)
        "RP": 0.15,   # Relief pitcher
        "CP": 0.25,   # Closer
        "C": 0.2,     # Catcher
        "1B": 0.15,   # First base
        "2B": 0.15,   # Second base
        "3B": 0.15,   # Third base
        "SS": 0.2,    # Shortstop
        "LF": 0.15,   # Left field
        "CF": 0.2,    # Center field
        "RF": 0.15,   # Right field
        "DH": 0.15,   # Designated hitter
        "P": 0.25,    # Generic pitcher
        "IF": 0.15,   # Generic infielder
        "OF": 0.15,   # Generic outfielder
    }
    
    def _normalize_team_name(self, team_name: str) -> Optional[str]:
        """Convert team name to SportsRadar team ID"""
        normalized = team_name.lower().strip()
        return self.TEAM_MAP.get(normalized)
    
    def _get_position_importance(self, position: str) -> float:
        """Get importance weight for MLB position"""
        return self.POSITION_WEIGHTS.get(position.upper(), 0.15)
    
    def _parse_team_stats(self, data: Dict) -> Dict:
        """Parse MLB team statistics from SportsRadar response"""
        team = data.get('team', data)
        stats = data.get('statistics', data.get('hitting', {}))
        
        # Parse record
        record = data.get('record', stats.get('record', {}))
        wins = record.get('wins', 0)
        losses = record.get('losses', 0)
        games_played = wins + losses
        
        # Parse batting stats
        batting = self._parse_batting_stats(data.get('hitting', stats))
        
        # Parse pitching stats
        pitching = self._parse_pitching_stats(data.get('pitching', {}))
        
        # Parse bullpen stats
        bullpen = self._parse_bullpen_stats(data.get('pitching', {}))
        
        return {
            'name': team.get('name', team.get('market', '')),
            'abbreviation': team.get('alias', ''),
            'record': {
                'wins': wins,
                'losses': losses,
                'win_percentage': wins / games_played if games_played > 0 else 0,
            },
            'batting': batting,
            'pitching': pitching,
            'bullpen': bullpen,
            'efficiency': {
                'run_differential': batting.get('runs_per_game', 0) - pitching.get('runs_allowed_per_game', 0),
                'offensive_efficiency': self._calculate_offensive_efficiency(batting),
                'pitching_efficiency': self._calculate_pitching_efficiency(pitching, bullpen),
            },
            'situational': {
                'home_record': self._parse_split_record(record.get('home', {})),
                'away_record': self._parse_split_record(record.get('road', {})),
            }
        }
    
    def _parse_batting_stats(self, hitting: Dict) -> Dict:
        """Parse MLB batting statistics"""
        games = max(1, hitting.get('games', {}).get('play', 1))
        overall = hitting.get('overall', hitting)
        
        return {
            'runs_per_game': overall.get('runs', {}).get('total', 0) / games,
            'batting_avg': overall.get('avg', 0),
            'on_base_pct': overall.get('obp', 0),
            'slugging_pct': overall.get('slg', 0),
            'ops': overall.get('ops', 0),
            'home_runs': overall.get('homeruns', overall.get('hr', 0)),
            'stolen_bases': overall.get('stolen_bases', overall.get('sb', 0)),
            'strikeout_rate': overall.get('ktotal', 0) / max(1, overall.get('ab', 1)),
            'walk_rate': overall.get('bb', 0) / max(1, overall.get('ab', 1)),
        }
    
    def _parse_pitching_stats(self, pitching: Dict) -> Dict:
        """Parse MLB pitching statistics"""
        games = max(1, pitching.get('games', {}).get('play', 1))
        overall = pitching.get('overall', pitching)
        starters = pitching.get('starters', {})
        
        return {
            'runs_allowed_per_game': overall.get('runs', {}).get('total', 0) / games,
            'era': overall.get('era', 0),
            'whip': overall.get('whip', 0),
            'strikeouts_per_9': overall.get('k9', overall.get('ktotal', 0) / max(1, overall.get('ip_1', 1)) * 9),
            'walks_per_9': overall.get('bb9', overall.get('bb', 0) / max(1, overall.get('ip_1', 1)) * 9),
            'hits_per_9': overall.get('h9', 0),
            'starter_era': starters.get('era', overall.get('era', 0)),
            'quality_starts': starters.get('quality_starts', 0),
        }
    
    def _parse_bullpen_stats(self, pitching: Dict) -> Dict:
        """Parse MLB bullpen/relief pitching statistics"""
        bullpen = pitching.get('bullpen', pitching.get('relief', {}))
        
        return {
            'bullpen_era': bullpen.get('era', 4.00),
            'bullpen_whip': bullpen.get('whip', 1.30),
            'saves': bullpen.get('saves', 0),
            'blown_saves': bullpen.get('blown_saves', 0),
            'holds': bullpen.get('holds', 0),
            'inherited_runners_scored_pct': bullpen.get('irs_pct', 0),
        }
    
    def _parse_split_record(self, split: Dict) -> Dict:
        """Parse a record split (home/away)"""
        return {
            'wins': split.get('wins', 0),
            'losses': split.get('losses', 0),
        }
    
    def _calculate_offensive_efficiency(self, batting: Dict) -> float:
        """
        Calculate offensive efficiency score (0-100).
        MLB-specific: OPS, runs, power.
        """
        # OPS (league avg ~.720)
        ops = batting.get('ops', 0.720)
        ops_score = min(100, (ops / 0.900) * 100)
        
        # Runs per game (league avg ~4.5)
        rpg = batting.get('runs_per_game', 4.5)
        rpg_score = min(100, (rpg / 6.0) * 100)
        
        # Walk rate (discipline)
        walk_rate = batting.get('walk_rate', 0.08)
        walk_score = min(100, walk_rate * 500)
        
        efficiency = (ops_score * 0.5 + rpg_score * 0.35 + walk_score * 0.15)
        return round(max(0, min(100, efficiency)), 1)
    
    def _calculate_pitching_efficiency(self, pitching: Dict, bullpen: Dict) -> float:
        """
        Calculate pitching efficiency score (0-100).
        MLB-specific: ERA, WHIP, K rate, bullpen.
        """
        # ERA (lower is better, league avg ~4.00)
        era = pitching.get('era', 4.00)
        era_score = min(100, max(0, (5.0 - era) / 3.0 * 100))
        
        # WHIP (lower is better, league avg ~1.25)
        whip = pitching.get('whip', 1.25)
        whip_score = min(100, max(0, (1.5 - whip) / 0.5 * 100))
        
        # Strikeouts per 9 (higher is better, league avg ~8.5)
        k9 = pitching.get('strikeouts_per_9', 8.5)
        k_score = min(100, k9 * 8)
        
        # Bullpen ERA
        bp_era = bullpen.get('bullpen_era', 4.00)
        bp_score = min(100, max(0, (5.0 - bp_era) / 3.0 * 100))
        
        efficiency = (era_score * 0.35 + whip_score * 0.25 + k_score * 0.2 + bp_score * 0.2)
        return round(max(0, min(100, efficiency)), 1)
    
    async def get_starting_pitcher(self, team_name: str, game_date: str = None) -> Optional[Dict]:
        """
        Get the probable starting pitcher for a team.
        
        Args:
            team_name: Team name
            game_date: Date of the game (YYYY-MM-DD format)
        
        Returns:
            Starting pitcher info with ERA, WHIP, recent performance
        """
        team_id = self._normalize_team_name(team_name)
        if not team_id:
            return None
        
        cache_key = self._make_cache_key("starting_pitcher", team_id, game_date)
        
        async def fetch_pitcher():
            # This would need the specific game endpoint
            # For now, return team's overall starter stats
            endpoint = f"teams/{team_id}/profile.json"
            data = await self._make_request(endpoint)
            if data:
                pitching = data.get('pitching', {})
                starters = pitching.get('starters', {})
                return {
                    'starter_era': starters.get('era', 4.00),
                    'starter_whip': starters.get('whip', 1.30),
                    'quality_start_rate': starters.get('quality_starts', 0) / max(1, starters.get('games', 1)),
                }
            return None
        
        return await self.fetch_with_fallback(
            cache_key=cache_key,
            primary_fn=fetch_pitcher,
            cache_ttl=self.CACHE_TTL_STATS
        )


# Factory function for easy import
@lru_cache(maxsize=1)
def get_mlb_fetcher() -> SportsRadarMLB:
    """Get an instance of the MLB SportsRadar fetcher"""
    return SportsRadarMLB()

