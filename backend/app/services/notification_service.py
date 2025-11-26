"""Notification service for email and in-app notifications"""

from typing import Dict, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
import secrets

from app.core.config import settings
from app.models.user import User
from app.models.parlay import Parlay


class NotificationService:
    """Service for sending notifications"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._email_enabled = bool(settings.openai_api_key)  # Can use Resend API key if available
    
    async def send_parlay_generated_notification(
        self,
        user: User,
        parlay: Parlay
    ) -> bool:
        """
        Send notification when parlay is generated
        
        For now, just stores in database for in-app notifications
        In production, can integrate with Resend/SendGrid
        """
        # Store notification in database (can be fetched by frontend)
        # For now, we'll just log it
        print(f"Notification: User {user.email} generated parlay {parlay.id}")
        return True
    
    async def send_parlay_resolved_notification(
        self,
        user: User,
        parlay: Parlay,
        hit: bool
    ) -> bool:
        """Send notification when parlay is resolved"""
        status = "won" if hit else "lost"
        print(f"Notification: User {user.email}'s parlay {parlay.id} {status}")
        return True
    
    async def send_weekly_summary(
        self,
        user: User,
        stats: Dict
    ) -> bool:
        """Send weekly performance summary"""
        print(f"Weekly summary for {user.email}: {stats}")
        return True
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str
    ) -> bool:
        """
        Send email using Resend API (free tier: 3000 emails/month)
        
        Requires RESEND_API_KEY in environment
        """
        # Check if Resend API key is configured
        resend_api_key = getattr(settings, 'resend_api_key', None)
        if not resend_api_key:
            # Fallback: just log
            print(f"Email would be sent to {to_email}: {subject}")
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {resend_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "from": "F3 Parlay AI <noreply@f3parlay.ai>",
                        "to": [to_email],
                        "subject": subject,
                        "html": html_content
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return True
                else:
                    print(f"Failed to send email: {response.status_code} - {response.text}")
                    return False
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def generate_share_token(self) -> str:
        """Generate a unique share token"""
        return secrets.token_urlsafe(16)

