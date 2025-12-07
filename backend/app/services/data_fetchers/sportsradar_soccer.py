"""
SportsRadar Soccer API Client

Fetches Soccer-specific data:
- Team statistics (goals, xG, possession)
- League standings
- Game schedules and results
- Injury reports

Supports multiple leagues: EPL, MLS, La Liga, etc.
"""

from typing import Dict, Optional, List
import logging

from app.services.data_fetchers.sportsradar_base import SportsRadarBase

logger = logging.getLogger(__name__)


class SportsRadarSoccer(SportsRadarBase):
    """
    SportsRadar Soccer API client.
    
    Provides soccer-specific team stats including:
    - Goals scored/conceded
    - Expected goals (xG)
    - Possession %
    - Home/away form
    - Points per game
    """
    
    # Supported leagues with their API endpoints
    LEAGUES = {
        "epl": {"name": "English Premier League", "competition_id": "sr:competition:17"},
        "mls": {"name": "MLS", "competition_id": "sr:competition:242"},
        "la_liga": {"name": "La Liga", "competition_id": "sr:competition:8"},
        "bundesliga": {"name": "Bundesliga", "competition_id": "sr:competition:35"},
        "serie_a": {"name": "Serie A", "competition_id": "sr:competition:23"},
        "ligue_1": {"name": "Ligue 1", "competition_id": "sr:competition:34"},
    }
    
    def __init__(self, league: str = "epl"):
        super().__init__(sport_code=f"soccer_{league}")
        self.league = league.lower()
        self.league_info = self.LEAGUES.get(self.league, self.LEAGUES["epl"])
    
    @property
    def base_url(self) -> str:
        return "https://api.sportradar.us/soccer/trial/v4/en"
    
    # Soccer team mapping: name -> SportsRadar team ID
    # EPL teams (most common)
    TEAM_MAP = {
        # EPL
        "arsenal": "sr:competitor:42",
        "aston villa": "sr:competitor:40",
        "bournemouth": "sr:competitor:60",
        "brentford": "sr:competitor:53",
        "brighton": "sr:competitor:45",
        "brighton & hove albion": "sr:competitor:45",
        "chelsea": "sr:competitor:38",
        "crystal palace": "sr:competitor:44",
        "everton": "sr:competitor:48",
        "fulham": "sr:competitor:43",
        "liverpool": "sr:competitor:44",
        "luton town": "sr:competitor:67",
        "manchester city": "sr:competitor:17",
        "man city": "sr:competitor:17",
        "manchester united": "sr:competitor:35",
        "man united": "sr:competitor:35",
        "man utd": "sr:competitor:35",
        "newcastle": "sr:competitor:39",
        "newcastle united": "sr:competitor:39",
        "nottingham forest": "sr:competitor:50",
        "forest": "sr:competitor:50",
        "sheffield united": "sr:competitor:62",
        "tottenham": "sr:competitor:33",
        "tottenham hotspur": "sr:competitor:33",
        "spurs": "sr:competitor:33",
        "west ham": "sr:competitor:37",
        "west ham united": "sr:competitor:37",
        "wolves": "sr:competitor:3",
        "wolverhampton": "sr:competitor:3",
        "wolverhampton wanderers": "sr:competitor:3",
        "burnley": "sr:competitor:36",
        "ipswich": "sr:competitor:46",
        "ipswich town": "sr:competitor:46",
        "leicester": "sr:competitor:31",
        "leicester city": "sr:competitor:31",
        "southampton": "sr:competitor:45",
        
        # MLS
        "la galaxy": "sr:competitor:4365",
        "lafc": "sr:competitor:66878",
        "los angeles fc": "sr:competitor:66878",
        "atlanta united": "sr:competitor:34316",
        "inter miami": "sr:competitor:132896",
        "miami": "sr:competitor:132896",
        "new york red bulls": "sr:competitor:4364",
        "red bulls": "sr:competitor:4364",
        "nyfc": "sr:competitor:37863",
        "new york city fc": "sr:competitor:37863",
        "seattle sounders": "sr:competitor:4384",
        "sounders": "sr:competitor:4384",
        "portland timbers": "sr:competitor:4368",
        "timbers": "sr:competitor:4368",
        "austin fc": "sr:competitor:217605",
        "columbus crew": "sr:competitor:4360",
        "crew": "sr:competitor:4360",
        "philadelphia union": "sr:competitor:4377",
        "union": "sr:competitor:4377",
        "fc cincinnati": "sr:competitor:103117",
        "cincinnati": "sr:competitor:103117",
        "nashville sc": "sr:competitor:131907",
        "nashville": "sr:competitor:131907",
        "orlando city": "sr:competitor:34283",
        "orlando": "sr:competitor:34283",
        "charlotte fc": "sr:competitor:204159",
        "charlotte": "sr:competitor:204159",
        "sporting kansas city": "sr:competitor:4382",
        "sporting kc": "sr:competitor:4382",
        "real salt lake": "sr:competitor:4378",
        "rsl": "sr:competitor:4378",
        "houston dynamo": "sr:competitor:4374",
        "dynamo": "sr:competitor:4374",
        "minnesota united": "sr:competitor:43960",
        "minnesota": "sr:competitor:43960",
        "colorado rapids": "sr:competitor:4361",
        "rapids": "sr:competitor:4361",
        "vancouver whitecaps": "sr:competitor:4385",
        "whitecaps": "sr:competitor:4385",
        "toronto fc": "sr:competitor:4383",
        "tfc": "sr:competitor:4383",
        "dc united": "sr:competitor:4362",
        "cf montreal": "sr:competitor:4370",
        "montreal": "sr:competitor:4370",
        "new england revolution": "sr:competitor:4367",
        "revolution": "sr:competitor:4367",
        "chicago fire": "sr:competitor:4359",
        "fire": "sr:competitor:4359",
        "st louis city": "sr:competitor:218259",
        "st louis": "sr:competitor:218259",
        "san jose earthquakes": "sr:competitor:4379",
        "earthquakes": "sr:competitor:4379",
    }
    
    # Soccer position importance weights
    POSITION_WEIGHTS = {
        "GK": 0.4,    # Goalkeeper
        "CB": 0.25,   # Center back
        "LB": 0.15,   # Left back
        "RB": 0.15,   # Right back
        "CDM": 0.2,   # Defensive midfielder
        "CM": 0.2,    # Central midfielder
        "CAM": 0.25,  # Attacking midfielder
        "LM": 0.15,   # Left midfielder
        "RM": 0.15,   # Right midfielder
        "LW": 0.2,    # Left winger
        "RW": 0.2,    # Right winger
        "ST": 0.35,   # Striker
        "CF": 0.3,    # Center forward
        "D": 0.2,     # Generic defender
        "M": 0.2,     # Generic midfielder
        "F": 0.3,     # Generic forward
    }
    
    def _normalize_team_name(self, team_name: str) -> Optional[str]:
        """Convert team name to SportsRadar team ID"""
        normalized = team_name.lower().strip()
        return self.TEAM_MAP.get(normalized)
    
    def _get_position_importance(self, position: str) -> float:
        """Get importance weight for soccer position"""
        return self.POSITION_WEIGHTS.get(position.upper(), 0.15)
    
    def _parse_team_stats(self, data: Dict) -> Dict:
        """Parse soccer team statistics from SportsRadar response"""
        team = data.get('team', data.get('competitor', data))
        stats = data.get('statistics', {})
        
        # Parse record/standings
        standing = data.get('standing', {})
        played = standing.get('played', 0)
        wins = standing.get('win', standing.get('wins', 0))
        draws = standing.get('draw', standing.get('draws', 0))
        losses = standing.get('loss', standing.get('losses', 0))
        
        # Parse goals
        goals_for = standing.get('goals_for', stats.get('goals_scored', 0))
        goals_against = standing.get('goals_against', stats.get('goals_conceded', 0))
        
        # Parse offensive stats
        offense = self._parse_offense_stats(stats)
        
        # Parse defensive stats
        defense = self._parse_defense_stats(stats)
        
        return {
            'name': team.get('name', ''),
            'abbreviation': team.get('abbreviation', team.get('short_name', '')),
            'record': {
                'played': played,
                'wins': wins,
                'draws': draws,
                'losses': losses,
                'points': wins * 3 + draws,
                'points_per_game': (wins * 3 + draws) / max(1, played),
                'win_percentage': wins / max(1, played),
            },
            'goals': {
                'scored': goals_for,
                'conceded': goals_against,
                'per_game': goals_for / max(1, played),
                'conceded_per_game': goals_against / max(1, played),
                'differential': goals_for - goals_against,
            },
            'offense': offense,
            'defense': defense,
            'efficiency': {
                'goal_differential': goals_for - goals_against,
                'offensive_efficiency': self._calculate_offensive_efficiency(offense, goals_for, played),
                'defensive_efficiency': self._calculate_defensive_efficiency(defense, goals_against, played),
            },
            'situational': {
                'home_form': self._parse_form(stats.get('home', {})),
                'away_form': self._parse_form(stats.get('away', {})),
            }
        }
    
    def _parse_offense_stats(self, stats: Dict) -> Dict:
        """Parse soccer offensive statistics"""
        return {
            'xg': stats.get('expected_goals', stats.get('xg', 0)),
            'shots': stats.get('shots_total', 0),
            'shots_on_target': stats.get('shots_on_target', 0),
            'shot_accuracy': stats.get('shot_accuracy', 0),
            'possession_avg': stats.get('possession', stats.get('ball_possession', 50)),
            'passes_completed': stats.get('passes_successful', 0),
            'pass_accuracy': stats.get('pass_accuracy', 0),
            'corners': stats.get('corner_kicks', 0),
        }
    
    def _parse_defense_stats(self, stats: Dict) -> Dict:
        """Parse soccer defensive statistics"""
        return {
            'xg_against': stats.get('expected_goals_against', stats.get('xga', 0)),
            'clean_sheets': stats.get('clean_sheets', 0),
            'saves': stats.get('saves', 0),
            'tackles': stats.get('tackles_total', stats.get('tackles', 0)),
            'interceptions': stats.get('interceptions', 0),
            'blocks': stats.get('blocked_shots', stats.get('blocks', 0)),
            'fouls_committed': stats.get('fouls', 0),
            'yellow_cards': stats.get('yellow_cards', 0),
            'red_cards': stats.get('red_cards', 0),
        }
    
    def _parse_form(self, form_stats: Dict) -> Dict:
        """Parse home/away form statistics"""
        played = form_stats.get('played', form_stats.get('games', 0))
        wins = form_stats.get('wins', form_stats.get('win', 0))
        draws = form_stats.get('draws', form_stats.get('draw', 0))
        losses = form_stats.get('losses', form_stats.get('loss', 0))
        
        return {
            'played': played,
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'points_per_game': (wins * 3 + draws) / max(1, played),
            'win_percentage': wins / max(1, played),
        }
    
    def _calculate_offensive_efficiency(self, offense: Dict, goals: int, games: int) -> float:
        """
        Calculate offensive efficiency score (0-100).
        Soccer-specific: xG, goals, possession, shot accuracy.
        """
        if games == 0:
            return 50.0
        
        # Goals per game (league avg ~1.5)
        gpg = goals / games
        gpg_score = min(100, (gpg / 2.5) * 100)
        
        # xG (expected goals, higher is better)
        xg = offense.get('xg', gpg * games) / max(1, games)
        xg_score = min(100, (xg / 2.0) * 100)
        
        # Shot accuracy (% of shots on target)
        shot_acc = offense.get('shot_accuracy', 35)
        shot_score = min(100, shot_acc * 2)
        
        # Possession (50% is neutral, 60%+ is dominant)
        possession = offense.get('possession_avg', 50)
        poss_score = min(100, (possession - 30) * 2.5)
        
        efficiency = (gpg_score * 0.35 + xg_score * 0.3 + shot_score * 0.2 + poss_score * 0.15)
        return round(max(0, min(100, efficiency)), 1)
    
    def _calculate_defensive_efficiency(self, defense: Dict, goals_against: int, games: int) -> float:
        """
        Calculate defensive efficiency score (0-100).
        Soccer-specific: goals against, clean sheets, xG against.
        """
        if games == 0:
            return 50.0
        
        # Goals against per game (lower is better, avg ~1.3)
        gapg = goals_against / games
        gapg_score = min(100, max(0, (2.5 - gapg) / 2.0 * 100))
        
        # Clean sheets percentage
        cs = defense.get('clean_sheets', 0)
        cs_pct = cs / games
        cs_score = min(100, cs_pct * 200)
        
        # xG against (lower is better)
        xga = defense.get('xg_against', gapg * games) / max(1, games)
        xga_score = min(100, max(0, (2.0 - xga) / 1.5 * 100))
        
        efficiency = (gapg_score * 0.4 + cs_score * 0.3 + xga_score * 0.3)
        return round(max(0, min(100, efficiency)), 1)
    
    async def get_league_standings(self, league: str = None) -> List[Dict]:
        """
        Get current league standings.
        
        Args:
            league: League code (epl, mls, etc.)
        
        Returns:
            List of teams with standings info
        """
        league_code = league or self.league
        league_info = self.LEAGUES.get(league_code, self.league_info)
        
        cache_key = self._make_cache_key("standings", league_code)
        
        async def fetch_standings():
            competition_id = league_info["competition_id"]
            endpoint = f"competitions/{competition_id}/standings.json"
            data = await self._make_request(endpoint)
            if data:
                return self._parse_standings(data)
            return []
        
        result = await self.fetch_with_fallback(
            cache_key=cache_key,
            primary_fn=fetch_standings,
            cache_ttl=self.CACHE_TTL_SCHEDULE
        )
        return result or []
    
    def _parse_standings(self, data: Dict) -> List[Dict]:
        """Parse league standings"""
        standings = []
        
        for group in data.get('standings', []):
            for team_standing in group.get('groups', [{}])[0].get('standings', []):
                team = team_standing.get('competitor', {})
                standings.append({
                    'rank': team_standing.get('rank', 0),
                    'team': team.get('name', ''),
                    'played': team_standing.get('played', 0),
                    'wins': team_standing.get('win', 0),
                    'draws': team_standing.get('draw', 0),
                    'losses': team_standing.get('loss', 0),
                    'points': team_standing.get('points', 0),
                    'goals_for': team_standing.get('goals_for', 0),
                    'goals_against': team_standing.get('goals_against', 0),
                    'goal_difference': team_standing.get('goal_diff', 0),
                })
        
        return sorted(standings, key=lambda x: x['rank'])


# Factory functions for easy import
def get_soccer_fetcher(league: str = "epl") -> SportsRadarSoccer:
    """Get an instance of the Soccer SportsRadar fetcher for a specific league"""
    return SportsRadarSoccer(league=league)


def get_epl_fetcher() -> SportsRadarSoccer:
    """Get an EPL-specific fetcher"""
    return SportsRadarSoccer(league="epl")


def get_mls_fetcher() -> SportsRadarSoccer:
    """Get an MLS-specific fetcher"""
    return SportsRadarSoccer(league="mls")

