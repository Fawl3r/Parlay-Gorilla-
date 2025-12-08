"""
Parlay Tips Service for generating betting strategy tips.

Provides:
- Free tier: Static, generic tips
- Premium tier: AI-personalized tips based on user history

Tips cover:
- Bankroll management
- Leg selection strategies
- Risk management
- Sport-specific advice
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
import logging

from app.models.parlay import Parlay
from app.models.user import User
from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)


# Static tips for free tier users
FREE_TIER_TIPS = [
    {
        "id": "bankroll_1",
        "category": "bankroll",
        "title": "Manage Your Bankroll",
        "tip": "Never bet more than 1-5% of your total bankroll on a single parlay. This protects you during losing streaks.",
        "icon": "💰"
    },
    {
        "id": "legs_1",
        "category": "strategy",
        "title": "Keep Parlays Tight",
        "tip": "3-4 leg parlays offer a good balance of payout potential and win probability. Avoid 10+ leg parlays unless you're feeling lucky.",
        "icon": "🎯"
    },
    {
        "id": "correlated_1",
        "category": "strategy",
        "title": "Look for Correlated Bets",
        "tip": "Correlated legs (like a team winning AND the over hitting in a blowout) can increase your edge when books don't adjust properly.",
        "icon": "🔗"
    },
    {
        "id": "value_1",
        "category": "value",
        "title": "Chase Value, Not Favorites",
        "tip": "Heavy favorites at -300 or worse rarely provide good parlay value. Look for plus-money underdogs with genuine upset potential.",
        "icon": "📈"
    },
    {
        "id": "research_1",
        "category": "research",
        "title": "Check Injury Reports",
        "tip": "Always check injury reports before locking in bets. A key player being out can swing a game 3-7 points.",
        "icon": "🏥"
    },
    {
        "id": "timing_1",
        "category": "timing",
        "title": "Bet Early for Best Lines",
        "tip": "Opening lines often have the most value. Sharp bettors move lines quickly, so early birds get the best odds.",
        "icon": "⏰"
    },
    {
        "id": "emotions_1",
        "category": "mindset",
        "title": "Avoid Emotional Betting",
        "tip": "Never chase losses with bigger bets. Take a break if you're on a losing streak - the games will still be there tomorrow.",
        "icon": "🧘"
    },
    {
        "id": "spreads_1",
        "category": "markets",
        "title": "Spreads vs Moneylines",
        "tip": "For favorites, spreads often offer better value than moneylines. A -7 spread pays better than -280 moneyline for similar risk.",
        "icon": "📊"
    },
]


class ParlayTipsService:
    """
    Service for generating parlay building tips.
    
    Free users get static generic tips.
    Premium users get AI-personalized tips based on their betting history.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.openai_service = OpenAIService()
    
    async def get_parlay_tips(
        self,
        user_id: Optional[str] = None,
        is_premium: bool = False,
        limit: int = 5,
        sport: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get parlay tips based on user tier.
        
        Args:
            user_id: User ID (optional)
            is_premium: Whether user has premium subscription
            limit: Maximum number of tips to return
            sport: Filter tips by sport (optional)
        
        Returns:
            Dict with tips array and metadata
        """
        if is_premium and user_id:
            # Generate personalized AI tips for premium users
            return await self._get_premium_tips(user_id, limit, sport)
        else:
            # Return static tips for free users
            return self._get_free_tips(limit, sport)
    
    def _get_free_tips(
        self,
        limit: int = 5,
        sport: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get static tips for free tier users."""
        tips = FREE_TIER_TIPS[:limit]
        
        return {
            "tier": "free",
            "tips": tips,
            "personalized": False,
            "message": "Upgrade to Premium for AI-personalized tips based on your betting style!",
            "upgrade_cta": True,
        }
    
    async def _get_premium_tips(
        self,
        user_id: str,
        limit: int = 5,
        sport: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate AI-personalized tips for premium users."""
        try:
            # Analyze user's betting history
            user_profile = await self._analyze_user_profile(user_id)
            
            # Generate personalized tips
            tips = await self._generate_ai_tips(user_profile, limit, sport)
            
            return {
                "tier": "premium",
                "tips": tips,
                "personalized": True,
                "profile_summary": user_profile.get("summary", ""),
                "upgrade_cta": False,
            }
            
        except Exception as e:
            logger.error(f"Error generating premium tips: {e}")
            # Fallback to free tips with premium wrapper
            return {
                "tier": "premium",
                "tips": FREE_TIER_TIPS[:limit],
                "personalized": False,
                "error": "Unable to personalize tips at this time",
                "upgrade_cta": False,
            }
    
    async def _analyze_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Analyze user's betting history to build a profile."""
        try:
            # Get user's recent parlays
            stmt = (
                select(Parlay)
                .where(Parlay.user_id == user_id)
                .order_by(desc(Parlay.created_at))
                .limit(50)
            )
            result = await self.db.execute(stmt)
            parlays = list(result.scalars().all())
            
            if not parlays:
                return {
                    "total_parlays": 0,
                    "summary": "New user - no betting history yet",
                    "preferences": {},
                }
            
            # Analyze patterns
            total = len(parlays)
            
            # Count legs per parlay
            leg_counts = []
            sports = {}
            risk_levels = {"conservative": 0, "balanced": 0, "aggressive": 0}
            
            for parlay in parlays:
                legs = parlay.legs if hasattr(parlay, 'legs') and parlay.legs else []
                leg_count = len(legs) if isinstance(legs, list) else 0
                leg_counts.append(leg_count)
                
                # Track sports (from legs data)
                for leg in (legs if isinstance(legs, list) else []):
                    sport = leg.get('sport', 'unknown') if isinstance(leg, dict) else 'unknown'
                    sports[sport] = sports.get(sport, 0) + 1
                
                # Estimate risk level
                if leg_count <= 3:
                    risk_levels["conservative"] += 1
                elif leg_count <= 6:
                    risk_levels["balanced"] += 1
                else:
                    risk_levels["aggressive"] += 1
            
            avg_legs = sum(leg_counts) / len(leg_counts) if leg_counts else 0
            
            # Determine dominant risk profile
            risk_profile = max(risk_levels, key=risk_levels.get)
            
            # Top sports
            top_sports = sorted(sports.items(), key=lambda x: x[1], reverse=True)[:3]
            
            return {
                "total_parlays": total,
                "avg_legs": round(avg_legs, 1),
                "risk_profile": risk_profile,
                "risk_distribution": risk_levels,
                "top_sports": [s[0] for s in top_sports],
                "preferences": {
                    "preferred_leg_count": round(avg_legs),
                    "sports": top_sports,
                },
                "summary": f"{'Aggressive' if risk_profile == 'aggressive' else 'Conservative' if risk_profile == 'conservative' else 'Balanced'} bettor with avg {round(avg_legs, 1)} legs per parlay",
            }
            
        except Exception as e:
            logger.error(f"Error analyzing user profile: {e}")
            return {
                "total_parlays": 0,
                "summary": "Unable to analyze history",
                "preferences": {},
            }
    
    async def _generate_ai_tips(
        self,
        user_profile: Dict[str, Any],
        limit: int,
        sport: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Generate AI-personalized tips based on user profile."""
        
        if user_profile.get("total_parlays", 0) < 3:
            # Not enough history, return enhanced static tips
            return [
                {
                    "id": "welcome",
                    "category": "personalized",
                    "title": "Welcome to Premium!",
                    "tip": "Build a few more parlays and we'll personalize tips based on your betting style.",
                    "icon": "🦍"
                }
            ] + FREE_TIER_TIPS[:limit-1]
        
        prompt = f"""You are Parlay Gorilla's personalized betting advisor. Generate {limit} specific, actionable tips for this user:

USER PROFILE:
- Total parlays built: {user_profile.get('total_parlays', 0)}
- Average legs per parlay: {user_profile.get('avg_legs', 3)}
- Risk profile: {user_profile.get('risk_profile', 'balanced')}
- Top sports: {', '.join(user_profile.get('top_sports', ['Various']))}
{f'- Current sport focus: {sport}' if sport else ''}

Generate {limit} personalized tips that:
1. Address their specific risk profile
2. Relate to their preferred sports
3. Help them improve based on their betting patterns
4. Include specific strategies they might not know

Format each tip as JSON with keys: id (unique string), category, title (short), tip (2-3 sentences), icon (single emoji)

Return as a JSON array. Do NOT include any markdown formatting or code blocks.

IMPORTANT: Never guarantee wins. All tips are for educational purposes only."""

        try:
            response = await self.openai_service.client.chat.completions.create(
                model=self.openai_service.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a sports betting strategy advisor. Provide helpful tips without guaranteeing outcomes. Return only valid JSON arrays."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.8,
                max_tokens=600,
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON response
            import json
            
            # Clean up potential markdown
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            tips = json.loads(content)
            
            if isinstance(tips, list):
                return tips[:limit]
            else:
                logger.warning("AI tips response was not a list")
                return FREE_TIER_TIPS[:limit]
                
        except Exception as e:
            logger.error(f"Error generating AI tips: {e}")
            return FREE_TIER_TIPS[:limit]


# Factory function
def get_parlay_tips_service(db: AsyncSession) -> ParlayTipsService:
    """Get an instance of ParlayTipsService."""
    return ParlayTipsService(db)

