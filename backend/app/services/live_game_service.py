"""
Live Game Service for real-time game tracking.

Handles:
- Fetching live game state from ESPN (API-Sports does not provide live play-by-play/drive tracking)
- Updating game scores and status
- Tracking drives/possessions
- Triggering notifications for score changes

Note: API-Sports provides fixture status (live/finished) but not detailed live data.
ESPN is used for live scores and drive tracking.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
import httpx
import logging

from app.core.config import settings
from app.models.live_game import LiveGame, LiveGameStatus
from app.models.drive import Drive, DriveResult
from app.services.data_fetchers.espn_scraper import ESPNScraper, get_espn_scraper

logger = logging.getLogger(__name__)


class LiveGameService:
    """
    Service for managing live game state and drive tracking.
    
    Uses ESPN scraper for live game data (API-Sports does not provide live play-by-play/drive tracking).
    Stores state in database and triggers Telegram notifications when scores change or drives complete.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.timeout = 15.0
        
        # ESPN scraper for live data
        self.espn = get_espn_scraper()
    
    async def update_live_game_state(
        self,
        game_id: str,
        external_game_id: Optional[str] = None
    ) -> Tuple[Optional[LiveGame], bool, bool]:
        """
        Fetch latest game state from ESPN and update database.
        
        Args:
            game_id: Internal game ID (UUID)
            external_game_id: External game ID (optional if fetching by internal ID)
        
        Returns:
            Tuple of (LiveGame, score_changed: bool, status_changed: bool)
        """
        try:
            # Get existing game from database
            game = await self._get_live_game(game_id)
            if not game:
                logger.warning(f"Live game not found: {game_id}")
                return None, False, False
            
            # Use external ID from database if not provided
            ext_id = external_game_id or game.external_game_id
            if not ext_id:
                logger.warning(f"No external game ID for: {game_id}")
                return game, False, False
            
            # Fetch live data from ESPN (API-Sports does not provide live play-by-play)
            live_data = await self._fetch_live_game_data(game.sport, ext_id)
            if not live_data:
                logger.warning(f"Failed to fetch live data for: {ext_id}")
                return game, False, False
            
            # Track changes
            old_score = (game.home_score, game.away_score)
            old_status = game.status
            
            # Update game state
            self._update_game_from_api(game, live_data)
            
            # Check what changed
            new_score = (game.home_score, game.away_score)
            score_changed = old_score != new_score
            status_changed = old_status != game.status
            
            # Save to database
            await self.db.commit()
            await self.db.refresh(game)
            
            logger.info(
                f"Updated live game {ext_id}: {game.away_team} {game.away_score} - "
                f"{game.home_score} {game.home_team} ({game.status})"
            )
            
            return game, score_changed, status_changed
            
        except Exception as e:
            logger.error(f"Error updating live game state: {e}")
            await self.db.rollback()
            return None, False, False
    
    async def sync_game_drives(
        self,
        game_id: str,
        external_game_id: Optional[str] = None
    ) -> List[Drive]:
        """
        Fetch drive data from ESPN and sync to database.
        Only inserts new drives that don't already exist.
        
        Args:
            game_id: Internal game ID (UUID)
            external_game_id: External game ID (optional)
        
        Returns:
            List of newly created Drive objects
        """
        try:
            # Get existing game
            game = await self._get_live_game(game_id)
            if not game:
                return []
            
            ext_id = external_game_id or game.external_game_id
            if not ext_id:
                return []
            
            # Fetch drive data from API
            drives_data = await self._fetch_drive_data(game.sport, ext_id)
            if not drives_data:
                return []
            
            # Get existing drive IDs
            existing_ids = await self._get_existing_drive_ids(game_id)
            
            # Create new drives
            new_drives = []
            for drive_data in drives_data:
                ext_drive_id = drive_data.get('id') or drive_data.get('sequence')
                if ext_drive_id and str(ext_drive_id) in existing_ids:
                    continue
                
                drive = self._create_drive_from_api(game, drive_data)
                if drive:
                    self.db.add(drive)
                    new_drives.append(drive)
            
            if new_drives:
                await self.db.commit()
                for drive in new_drives:
                    await self.db.refresh(drive)
                logger.info(f"Added {len(new_drives)} new drives for game {ext_id}")
            
            return new_drives
            
        except Exception as e:
            logger.error(f"Error syncing game drives: {e}")
            await self.db.rollback()
            return []
    
    async def get_live_game_with_drives(
        self,
        game_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get full live game state including all drives.
        
        Returns:
            Dict with game info and drives list
        """
        try:
            # Query with drives loaded
            stmt = (
                select(LiveGame)
                .options(selectinload(LiveGame.drives))
                .where(LiveGame.id == game_id)
            )
            result = await self.db.execute(stmt)
            game = result.scalar_one_or_none()
            
            if not game:
                return None
            
            # Sort drives by drive_number
            sorted_drives = sorted(game.drives, key=lambda d: d.drive_number)
            
            return {
                "id": str(game.id),
                "external_game_id": game.external_game_id,
                "sport": game.sport,
                "home_team": game.home_team,
                "away_team": game.away_team,
                "home_score": game.home_score,
                "away_score": game.away_score,
                "status": game.status,
                "quarter": game.quarter,
                "period_name": game.period_name,
                "time_remaining": game.time_remaining,
                "scheduled_start": game.scheduled_start.isoformat() if game.scheduled_start else None,
                "last_updated_at": game.last_updated_at.isoformat() if game.last_updated_at else None,
                "drives": [
                    {
                        "id": str(d.id),
                        "drive_number": d.drive_number,
                        "team": d.team,
                        "quarter": d.quarter,
                        "result": d.result,
                        "points_scored": d.points_scored,
                        "description": d.description,
                        "home_score_after": d.home_score_after,
                        "away_score_after": d.away_score_after,
                    }
                    for d in sorted_drives
                ],
            }
            
        except Exception as e:
            logger.error(f"Error getting live game with drives: {e}")
            return None
    
    async def get_all_live_games(
        self,
        sport: Optional[str] = None,
        include_recent_finals: bool = True
    ) -> List[LiveGame]:
        """
        Get all games that are currently live or recently finished.
        
        Args:
            sport: Filter by sport (optional)
            include_recent_finals: Include games that ended in last 2 hours
        """
        try:
            conditions = [
                LiveGame.status.in_([
                    LiveGameStatus.in_progress.value,
                    LiveGameStatus.halftime.value,
                ])
            ]
            
            if include_recent_finals:
                # Include finals from last 2 hours
                from datetime import timedelta
                cutoff = datetime.now(timezone.utc) - timedelta(hours=2)
                conditions.append(
                    and_(
                        LiveGame.status == LiveGameStatus.final.value,
                        LiveGame.last_updated_at >= cutoff
                    )
                )
            
            # Combine with OR
            from sqlalchemy import or_
            stmt = select(LiveGame).where(or_(*conditions))
            
            if sport:
                stmt = stmt.where(LiveGame.sport == sport.lower())
            
            stmt = stmt.order_by(LiveGame.scheduled_start)
            
            result = await self.db.execute(stmt)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Error getting live games: {e}")
            return []
    
    async def create_live_game(
        self,
        external_game_id: str,
        sport: str,
        home_team: str,
        away_team: str,
        scheduled_start: Optional[datetime] = None,
    ) -> LiveGame:
        """Create a new live game entry."""
        game = LiveGame(
            external_game_id=external_game_id,
            sport=sport.lower(),
            home_team=home_team,
            away_team=away_team,
            scheduled_start=scheduled_start,
            status=LiveGameStatus.scheduled.value,
            home_score=0,
            away_score=0,
        )
        self.db.add(game)
        await self.db.commit()
        await self.db.refresh(game)
        return game
    
    # ==================== PRIVATE METHODS ====================
    
    async def _get_live_game(self, game_id: str) -> Optional[LiveGame]:
        """Get live game by ID."""
        result = await self.db.execute(
            select(LiveGame).where(LiveGame.id == game_id)
        )
        return result.scalar_one_or_none()
    
    async def _get_existing_drive_ids(self, game_id: str) -> set:
        """Get set of external drive IDs that already exist."""
        result = await self.db.execute(
            select(Drive.external_drive_id)
            .where(Drive.game_id == game_id)
            .where(Drive.external_drive_id.isnot(None))
        )
        return {str(r) for r in result.scalars().all() if r}
    
    async def _fetch_live_game_data(
        self,
        sport: str,
        external_game_id: str
    ) -> Optional[Dict]:
        """
        Fetch live game data from ESPN (API-Sports does not provide live play-by-play/drive tracking).
        
        Note: API-Sports provides fixture status (live/finished) but not detailed live scores,
        drive tracking, or play-by-play. ESPN is used for live game data.
        """
        try:
            # Use ESPN scraper for live game data
            # ESPN uses different identifiers, so we may need to map external_game_id
            # For now, return None and log that live data is not fully supported
            # TODO: Implement ESPN live game data fetching if needed
            logger.info(f"Live game data fetching via ESPN for {sport} game {external_game_id} (not yet fully implemented)")
            return None
        except Exception as e:
            logger.error(f"Error fetching live game data: {e}")
        
        return None
    
    async def _fetch_drive_data(
        self,
        sport: str,
        external_game_id: str
    ) -> List[Dict]:
        """
        Fetch drive/possession data from ESPN (API-Sports does not provide drive tracking).
        
        Note: API-Sports does not provide drive-by-drive or play-by-play data.
        ESPN would need to be implemented for drive tracking if this feature is required.
        For now, returns empty list.
        """
        # TODO: Implement ESPN drive tracking if needed
        # API-Sports does not provide drive/play-by-play data
        logger.debug(f"Drive tracking not yet implemented via ESPN for {sport} game {external_game_id}")
        return []
    
    def _update_game_from_api(self, game: LiveGame, data: Dict) -> None:
        """Update LiveGame model from API response data."""
        # Get status
        status_str = data.get('status', '').lower()
        if status_str in ['inprogress', 'in_progress', 'live']:
            game.status = LiveGameStatus.in_progress.value
        elif status_str in ['halftime', 'half']:
            game.status = LiveGameStatus.halftime.value
        elif status_str in ['closed', 'complete', 'final']:
            game.status = LiveGameStatus.final.value
        elif status_str in ['scheduled', 'created']:
            game.status = LiveGameStatus.scheduled.value
        elif status_str in ['postponed', 'delayed']:
            game.status = LiveGameStatus.postponed.value
        elif status_str in ['cancelled', 'canceled']:
            game.status = LiveGameStatus.cancelled.value
        
        # Get scores - handle different API response formats
        home_data = data.get('home', {})
        away_data = data.get('away', {})
        
        game.home_score = home_data.get('points', home_data.get('score', game.home_score))
        game.away_score = away_data.get('points', away_data.get('score', game.away_score))
        
        # Get period/quarter info
        game.quarter = data.get('quarter', data.get('period', game.quarter))
        game.time_remaining = data.get('clock', data.get('time', game.time_remaining))
        
        # Get period name
        if game.quarter:
            game.period_name = self._get_period_name(game.sport, game.quarter)
        
        # Update timestamp
        game.last_updated_at = datetime.now(timezone.utc)
    
    def _create_drive_from_api(self, game: LiveGame, data: Dict) -> Optional[Drive]:
        """Create Drive model from API response data."""
        try:
            # Get team info
            team_data = data.get('team', {})
            team_name = team_data.get('name', team_data.get('market', ''))
            is_home = team_name.lower() in game.home_team.lower()
            
            # Determine result
            result_str = data.get('result', '').lower()
            result = self._parse_drive_result(result_str)
            
            # Get points scored
            points = 0
            if result == DriveResult.touchdown.value:
                points = 6 + data.get('extra_point', 1)  # Assume XP
            elif result == DriveResult.field_goal.value:
                points = 3
            elif result == DriveResult.safety.value:
                points = 2
            
            # Calculate score after drive
            if is_home:
                home_after = game.home_score + points
                away_after = game.away_score
            else:
                home_after = game.home_score
                away_after = game.away_score + points
            
            return Drive(
                game_id=game.id,
                drive_number=data.get('sequence', data.get('drive_number', 0)),
                external_drive_id=str(data.get('id', data.get('sequence', ''))),
                team=team_name,
                team_id=team_data.get('id'),
                is_home_team=1 if is_home else 0,
                quarter=data.get('quarter'),
                start_time=data.get('start_clock'),
                end_time=data.get('end_clock'),
                start_yard_line=data.get('start_position', {}).get('yardline'),
                end_yard_line=data.get('end_position', {}).get('yardline'),
                yards_gained=data.get('net_yards', data.get('yards')),
                plays_count=data.get('play_count', len(data.get('plays', []))),
                result=result,
                points_scored=points,
                description=data.get('description', self._generate_drive_description(data)),
                home_score_after=home_after,
                away_score_after=away_after,
            )
            
        except Exception as e:
            logger.error(f"Error creating drive from API data: {e}")
            return None
    
    def _parse_drive_result(self, result_str: str) -> str:
        """Parse drive result string to DriveResult value."""
        result_lower = result_str.lower()
        
        if 'touchdown' in result_lower or 'td' in result_lower:
            return DriveResult.touchdown.value
        elif 'field goal' in result_lower or 'fg' in result_lower:
            return DriveResult.field_goal.value
        elif 'punt' in result_lower:
            return DriveResult.punt.value
        elif 'interception' in result_lower or 'fumble' in result_lower:
            return DriveResult.turnover.value
        elif 'downs' in result_lower:
            return DriveResult.turnover_on_downs.value
        elif 'safety' in result_lower:
            return DriveResult.safety.value
        elif 'half' in result_lower:
            return DriveResult.end_of_half.value
        elif 'game' in result_lower or 'final' in result_lower:
            return DriveResult.end_of_game.value
        else:
            return DriveResult.in_progress.value
    
    def _get_period_name(self, sport: str, period: int) -> str:
        """Get human-readable period name."""
        sport_lower = sport.lower()
        
        if sport_lower == 'nfl':
            return f"Q{period}" if period <= 4 else f"OT{period - 4}"
        elif sport_lower == 'nba':
            return f"Q{period}" if period <= 4 else f"OT{period - 4}"
        elif sport_lower == 'nhl':
            return f"P{period}" if period <= 3 else f"OT{period - 3}"
        elif sport_lower == 'mlb':
            return f"Inning {period}"
        else:
            return f"Period {period}"
    
    def _generate_drive_description(self, data: Dict) -> str:
        """Generate a description for a drive."""
        team = data.get('team', {}).get('name', 'Unknown')
        result = data.get('result', 'unknown')
        yards = data.get('net_yards', data.get('yards', 0))
        plays = data.get('play_count', len(data.get('plays', [])))
        
        return f"{team}: {plays} plays, {yards} yards - {result}"


# Factory function
def get_live_game_service(db: AsyncSession) -> LiveGameService:
    """Get an instance of LiveGameService."""
    return LiveGameService(db)

