"""
AI Live Insights Service for generating real-time game analysis.

Provides:
- Momentum analysis
- Probability commentary
- Key matchup shifts
- Risk profile updates
- Premium-only feature
"""

from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.config import settings
from app.services.live_game_service import LiveGameService
from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)


class LiveInsightsService:
    """
    Service for generating AI-powered live game insights.
    
    Uses live game state and drive data to generate real-time
    analysis and commentary for premium users.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.live_game_service = LiveGameService(db)
        self.openai_service = OpenAIService()
    
    async def generate_live_insights(
        self,
        game_id: str,
        include_betting_angles: bool = True
    ) -> Dict[str, Any]:
        """
        Generate AI-powered live insights for a game.
        
        Args:
            game_id: Internal game ID
            include_betting_angles: Include betting strategy notes
        
        Returns:
            Dict with insights sections
        """
        try:
            # Get live game data with drives
            game_data = await self.live_game_service.get_live_game_with_drives(game_id)
            
            if not game_data:
                return {
                    "error": "Game not found",
                    "game_id": game_id,
                }
            
            # Generate AI insights
            insights = await self._generate_ai_insights(game_data, include_betting_angles)
            
            return {
                "game_id": game_id,
                "matchup": f"{game_data['away_team']} @ {game_data['home_team']}",
                "score": f"{game_data['away_score']} - {game_data['home_score']}",
                "status": game_data['status'],
                "period": game_data.get('period_name'),
                "time_remaining": game_data.get('time_remaining'),
                "insights": insights,
                "generated_at": game_data.get('last_updated_at'),
            }
            
        except Exception as e:
            logger.error(f"Error generating live insights: {e}")
            return {
                "error": str(e),
                "game_id": game_id,
            }
    
    async def _generate_ai_insights(
        self,
        game_data: Dict[str, Any],
        include_betting_angles: bool = True
    ) -> Dict[str, Any]:
        """Generate AI insights using OpenAI."""
        
        # Build context from game data
        drives_summary = self._summarize_drives(game_data.get('drives', []))
        
        prompt = f"""Analyze this live {game_data['sport'].upper()} game and provide insights:

GAME: {game_data['away_team']} @ {game_data['home_team']}
SCORE: {game_data['away_team']} {game_data['away_score']} - {game_data['home_score']} {game_data['home_team']}
STATUS: {game_data['status']}
PERIOD: {game_data.get('period_name', 'Unknown')} - {game_data.get('time_remaining', '')}

RECENT DRIVES:
{drives_summary}

Provide analysis in these sections (be concise, 2-3 sentences each):

1. MOMENTUM: Which team has momentum right now and why?

2. KEY_FACTORS: What are the critical factors affecting this game?

3. PROBABILITY_SHIFT: How have win probabilities shifted based on game flow?

4. MATCHUP_ANALYSIS: What matchups are deciding this game?

{f'''5. BETTING_ANGLES: What live betting opportunities might exist? (Include spread, total, moneyline considerations)

IMPORTANT: Do NOT guarantee any betting outcomes. All suggestions are for informational purposes only.''' if include_betting_angles else ''}

Format your response as JSON with keys: momentum, key_factors, probability_shift, matchup_analysis{', betting_angles' if include_betting_angles else ''}"""

        try:
            response = await self.openai_service.client.chat.completions.create(
                model=self.openai_service.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are Parlay Gorilla's live game analyst. Provide insightful, data-driven analysis of live sports games. Be honest about uncertainty. Never guarantee outcomes."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=800,
            )
            
            content = response.choices[0].message.content.strip()
            
            # Try to parse as JSON, fallback to text sections
            try:
                import json
                # Clean up potential markdown formatting
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                insights = json.loads(content)
            except (json.JSONDecodeError, IndexError):
                # Parse as text sections
                insights = self._parse_text_insights(content)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating AI insights: {e}")
            return {
                "momentum": "Unable to generate analysis at this time.",
                "key_factors": "Please check back shortly.",
                "probability_shift": "Analysis unavailable.",
                "matchup_analysis": "Unable to analyze matchups.",
            }
    
    def _summarize_drives(self, drives: list, max_drives: int = 6) -> str:
        """Summarize recent drives for AI context."""
        if not drives:
            return "No drive data available."
        
        # Get most recent drives
        recent = drives[-max_drives:] if len(drives) > max_drives else drives
        
        summaries = []
        for drive in recent:
            summary = f"- {drive.get('team', 'Unknown')}: {drive.get('description', 'No details')}"
            if drive.get('points_scored'):
                summary += f" (+{drive['points_scored']} pts)"
            summaries.append(summary)
        
        return "\n".join(summaries) if summaries else "No recent drive activity."
    
    def _parse_text_insights(self, content: str) -> Dict[str, str]:
        """Parse text-based insights into sections."""
        insights = {}
        
        sections = {
            "momentum": ["MOMENTUM:", "1. MOMENTUM:"],
            "key_factors": ["KEY_FACTORS:", "2. KEY_FACTORS:"],
            "probability_shift": ["PROBABILITY_SHIFT:", "3. PROBABILITY_SHIFT:"],
            "matchup_analysis": ["MATCHUP_ANALYSIS:", "4. MATCHUP_ANALYSIS:"],
            "betting_angles": ["BETTING_ANGLES:", "5. BETTING_ANGLES:"],
        }
        
        for key, markers in sections.items():
            for marker in markers:
                if marker in content:
                    start = content.find(marker) + len(marker)
                    # Find the next section or end
                    end = len(content)
                    for other_key, other_markers in sections.items():
                        if other_key != key:
                            for other_marker in other_markers:
                                idx = content.find(other_marker, start)
                                if idx != -1 and idx < end:
                                    end = idx
                    insights[key] = content[start:end].strip()
                    break
        
        return insights


# Factory function
def get_live_insights_service(db: AsyncSession) -> LiveInsightsService:
    """Get an instance of LiveInsightsService."""
    return LiveInsightsService(db)

