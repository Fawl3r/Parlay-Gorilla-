"""
Telegram Bot Service for sending game updates.

Sends notifications for:
- Drive updates (scoring plays, key possessions)
- Score changes
- Final scores
- Game status changes

Requires environment variables:
- TELEGRAM_BOT_TOKEN: Your Telegram bot token from @BotFather
- TELEGRAM_DEFAULT_CHAT_ID: Default chat/channel ID for notifications
"""

from typing import Optional, List
import httpx
import logging
import os

logger = logging.getLogger(__name__)


class TelegramBotService:
    """
    Service for sending Telegram notifications about live game updates.
    
    Usage:
        bot = TelegramBotService()
        await bot.send_score_update(chat_id, "Chiefs 7 - Ravens 3")
    """
    
    BASE_URL = "https://api.telegram.org/bot"
    
    def __init__(self, bot_token: Optional[str] = None):
        """
        Initialize Telegram bot service.
        
        Args:
            bot_token: Telegram bot token. Falls back to TELEGRAM_BOT_TOKEN env var.
        """
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.default_chat_id = os.getenv("TELEGRAM_DEFAULT_CHAT_ID")
        self.timeout = 10.0
        
        if not self.bot_token:
            logger.warning("TELEGRAM_BOT_TOKEN not configured - notifications disabled")
    
    @property
    def is_configured(self) -> bool:
        """Check if the bot is properly configured."""
        return bool(self.bot_token)
    
    async def send_message(
        self,
        text: str,
        chat_id: Optional[str] = None,
        parse_mode: str = "HTML",
        disable_notification: bool = False,
    ) -> bool:
        """
        Send a message to a Telegram chat.
        
        Args:
            text: Message text (supports HTML formatting)
            chat_id: Target chat ID. Uses default if not specified.
            parse_mode: "HTML" or "Markdown"
            disable_notification: Send silently if True
        
        Returns:
            True if message was sent successfully
        """
        if not self.is_configured:
            logger.debug("Telegram not configured, skipping message")
            return False
        
        target_chat = chat_id or self.default_chat_id
        if not target_chat:
            logger.warning("No chat_id provided and no default configured")
            return False
        
        url = f"{self.BASE_URL}{self.bot_token}/sendMessage"
        
        payload = {
            "chat_id": target_chat,
            "text": text,
            "parse_mode": parse_mode,
            "disable_notification": disable_notification,
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("ok"):
                        logger.info(f"Telegram message sent to {target_chat}")
                        return True
                    else:
                        logger.warning(f"Telegram API error: {result.get('description')}")
                else:
                    logger.warning(f"Telegram HTTP error: {response.status_code}")
                    
        except httpx.TimeoutException:
            logger.warning("Telegram API timeout")
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
        
        return False
    
    async def send_drive_update(
        self,
        team: str,
        result: str,
        description: str,
        score_home: int,
        score_away: int,
        home_team: str,
        away_team: str,
        chat_id: Optional[str] = None,
    ) -> bool:
        """
        Send a drive update notification.
        
        Args:
            team: Team that had the possession
            result: Drive result (touchdown, field_goal, punt, etc.)
            description: Drive description
            score_home: Current home team score
            score_away: Current away team score
            home_team: Home team name
            away_team: Away team name
            chat_id: Target chat ID (optional)
        """
        # Select emoji based on result
        emoji = self._get_result_emoji(result)
        
        message = (
            f"{emoji} <b>Drive Update</b>\n\n"
            f"<b>{team}</b>: {description}\n\n"
            f"📊 <b>Score:</b> {away_team} {score_away} - {score_home} {home_team}"
        )
        
        return await self.send_message(message, chat_id)
    
    async def send_score_update(
        self,
        home_team: str,
        away_team: str,
        home_score: int,
        away_score: int,
        period: Optional[str] = None,
        time_remaining: Optional[str] = None,
        scoring_team: Optional[str] = None,
        points_scored: Optional[int] = None,
        chat_id: Optional[str] = None,
    ) -> bool:
        """
        Send a score change notification.
        
        Args:
            home_team: Home team name
            away_team: Away team name
            home_score: Current home team score
            away_score: Current away team score
            period: Current period/quarter (optional)
            time_remaining: Time remaining in period (optional)
            scoring_team: Team that scored (optional)
            points_scored: Points scored on this play (optional)
            chat_id: Target chat ID (optional)
        """
        # Build message
        header = "🚨 <b>SCORE UPDATE</b> 🚨\n\n"
        
        if scoring_team and points_scored:
            header = f"🎯 <b>{scoring_team} SCORES!</b> (+{points_scored})\n\n"
        
        score_line = f"<b>{away_team}</b> {away_score} - {home_score} <b>{home_team}</b>\n"
        
        time_line = ""
        if period:
            time_line = f"\n⏱ {period}"
            if time_remaining:
                time_line += f" | {time_remaining}"
        
        message = header + score_line + time_line
        
        return await self.send_message(message, chat_id)
    
    async def send_final_update(
        self,
        home_team: str,
        away_team: str,
        home_score: int,
        away_score: int,
        sport: str = "NFL",
        chat_id: Optional[str] = None,
    ) -> bool:
        """
        Send a final score notification.
        
        Args:
            home_team: Home team name
            away_team: Away team name
            home_score: Final home team score
            away_score: Final away team score
            sport: Sport type for context
            chat_id: Target chat ID (optional)
        """
        # Determine winner
        if home_score > away_score:
            winner = home_team
            emoji = "🏆"
        elif away_score > home_score:
            winner = away_team
            emoji = "🏆"
        else:
            winner = None
            emoji = "🤝"  # Tie
        
        message = (
            f"🏁 <b>FINAL</b> 🏁\n\n"
            f"<b>{away_team}</b> {away_score} - {home_score} <b>{home_team}</b>\n\n"
        )
        
        if winner:
            message += f"{emoji} <b>{winner} wins!</b>"
        else:
            message += f"{emoji} <b>Game ends in a tie!</b>"
        
        return await self.send_message(message, chat_id)
    
    async def send_game_start(
        self,
        home_team: str,
        away_team: str,
        sport: str = "NFL",
        chat_id: Optional[str] = None,
    ) -> bool:
        """
        Send a game starting notification.
        
        Args:
            home_team: Home team name
            away_team: Away team name
            sport: Sport type
            chat_id: Target chat ID (optional)
        """
        emoji = self._get_sport_emoji(sport)
        
        message = (
            f"{emoji} <b>GAME STARTING</b> {emoji}\n\n"
            f"<b>{away_team}</b> @ <b>{home_team}</b>\n\n"
            f"📺 Stay tuned for live updates!"
        )
        
        return await self.send_message(message, chat_id)
    
    async def send_halftime(
        self,
        home_team: str,
        away_team: str,
        home_score: int,
        away_score: int,
        chat_id: Optional[str] = None,
    ) -> bool:
        """
        Send a halftime score notification.
        
        Args:
            home_team: Home team name
            away_team: Away team name
            home_score: Home team score at half
            away_score: Away team score at half
            chat_id: Target chat ID (optional)
        """
        message = (
            f"⏸️ <b>HALFTIME</b> ⏸️\n\n"
            f"<b>{away_team}</b> {away_score} - {home_score} <b>{home_team}</b>\n\n"
            f"📊 Second half coming up..."
        )
        
        return await self.send_message(message, chat_id)
    
    async def broadcast_to_channels(
        self,
        text: str,
        chat_ids: List[str],
    ) -> int:
        """
        Send a message to multiple channels.
        
        Args:
            text: Message text
            chat_ids: List of chat IDs to send to
        
        Returns:
            Number of successful sends
        """
        success_count = 0
        for chat_id in chat_ids:
            if await self.send_message(text, chat_id):
                success_count += 1
        return success_count
    
    def _get_result_emoji(self, result: str) -> str:
        """Get emoji for drive result."""
        result_lower = result.lower()
        
        if 'touchdown' in result_lower:
            return "🎉🏈"
        elif 'field_goal' in result_lower or 'field goal' in result_lower:
            return "🥅"
        elif 'punt' in result_lower:
            return "👟"
        elif 'turnover' in result_lower or 'interception' in result_lower:
            return "↩️"
        elif 'safety' in result_lower:
            return "⚠️"
        elif 'fumble' in result_lower:
            return "🤲"
        else:
            return "📍"
    
    def _get_sport_emoji(self, sport: str) -> str:
        """Get emoji for sport type."""
        sport_lower = sport.lower()
        
        return {
            "nfl": "🏈",
            "nba": "🏀",
            "nhl": "🏒",
            "mlb": "⚾",
            "soccer": "⚽",
            "ncaaf": "🏈",
            "ncaab": "🏀",
        }.get(sport_lower, "🏆")


# Singleton instance
_telegram_service: Optional[TelegramBotService] = None


def get_telegram_service() -> TelegramBotService:
    """Get the singleton TelegramBotService instance."""
    global _telegram_service
    if _telegram_service is None:
        _telegram_service = TelegramBotService()
    return _telegram_service


# Convenience functions for quick access
async def send_drive_update(
    team: str,
    result: str,
    description: str,
    score_home: int,
    score_away: int,
    home_team: str,
    away_team: str,
    chat_id: Optional[str] = None,
) -> bool:
    """Quick function to send a drive update."""
    return await get_telegram_service().send_drive_update(
        team, result, description, score_home, score_away, 
        home_team, away_team, chat_id
    )


async def send_score_update(
    home_team: str,
    away_team: str,
    home_score: int,
    away_score: int,
    period: Optional[str] = None,
    time_remaining: Optional[str] = None,
    scoring_team: Optional[str] = None,
    points_scored: Optional[int] = None,
    chat_id: Optional[str] = None,
) -> bool:
    """Quick function to send a score update."""
    return await get_telegram_service().send_score_update(
        home_team, away_team, home_score, away_score,
        period, time_remaining, scoring_team, points_scored, chat_id
    )


async def send_final_update(
    home_team: str,
    away_team: str,
    home_score: int,
    away_score: int,
    sport: str = "NFL",
    chat_id: Optional[str] = None,
) -> bool:
    """Quick function to send a final score update."""
    return await get_telegram_service().send_final_update(
        home_team, away_team, home_score, away_score, sport, chat_id
    )

