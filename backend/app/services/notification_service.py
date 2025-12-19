"""Notification service for email and in-app notifications"""

from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import secrets
import logging

from app.core.config import settings
from app.models.user import User
from app.models.parlay import Parlay
from app.services.email_templates import (
    EmailBranding,
    PasswordResetEmailTemplate,
    VerificationEmailTemplate,
)

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications"""
    
    def __init__(self, db: AsyncSession = None):
        self.db = db
        self._email_enabled = bool(getattr(settings, 'resend_api_key', None))
    
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
        logger.info(f"Notification: User {user.email} generated parlay {parlay.id}")
        return True
    
    async def send_parlay_resolved_notification(
        self,
        user: User,
        parlay: Parlay,
        hit: bool
    ) -> bool:
        """Send notification when parlay is resolved"""
        status = "won" if hit else "lost"
        logger.info(f"Notification: User {user.email}'s parlay {parlay.id} {status}")
        return True
    
    async def send_weekly_summary(
        self,
        user: User,
        stats: Dict
    ) -> bool:
        """Send weekly performance summary"""
        logger.info(f"Weekly summary for {user.email}: {stats}")
        return True
    
    # =========================================================================
    # Email Verification
    # =========================================================================
    
    async def send_email_verification(
        self,
        user: User,
        verification_url: str
    ) -> bool:
        """
        Send email verification email.
        
        Args:
            user: User to send email to
            verification_url: Full URL for email verification (includes token)
        """
        branding = EmailBranding.parlay_gorilla(settings.app_url, settings.email_logo_url)
        template = VerificationEmailTemplate(branding)

        rendered = template.render(
            user_name=user.display_name or user.username or user.email.split("@")[0],
            verification_url=verification_url,
        )

        return await self.send_email(
            to_email=user.email,
            subject=rendered.subject,
            html_content=rendered.html,
            text_content=rendered.text,
        )
    
    # =========================================================================
    # Password Reset
    # =========================================================================
    
    async def send_password_reset(
        self,
        user: User,
        reset_url: str
    ) -> bool:
        """
        Send password reset email.
        
        Args:
            user: User to send email to
            reset_url: Full URL for password reset (includes token)
        """
        branding = EmailBranding.parlay_gorilla(settings.app_url, settings.email_logo_url)
        template = PasswordResetEmailTemplate(branding)

        rendered = template.render(
            user_name=user.display_name or user.username or user.email.split("@")[0],
            reset_url=reset_url,
        )

        return await self.send_email(
            to_email=user.email,
            subject=rendered.subject,
            html_content=rendered.html,
            text_content=rendered.text,
        )
    
    # =========================================================================
    # Generic Email Sending
    # =========================================================================
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """
        Send email using Resend API (free tier: 3000 emails/month)
        
        Requires RESEND_API_KEY in environment
        """
        # Check if Resend API key is configured
        resend_api_key = getattr(settings, 'resend_api_key', None)
        if not resend_api_key:
            # Log warning that email cannot be sent
            logger.warning(
                f"⚠️  EMAIL NOT SENT: RESEND_API_KEY not configured. "
                f"Would send to {to_email}: {subject}"
            )
            logger.warning(
                "To enable email sending, set RESEND_API_KEY in your environment variables. "
                "Get a free API key at https://resend.com"
            )
            return False
        
        # Resend "from" address must be a verified domain OR a Resend-provided address (onboarding@resend.dev).
        resend_from = (getattr(settings, "resend_from", None) or "").strip()
        if not resend_from:
            resend_from = "Parlay Gorilla <onboarding@resend.dev>"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {resend_api_key}",
                        "Content-Type": "application/json"
                    },
                    json=self._build_resend_payload(
                        resend_from=resend_from,
                        to_email=to_email,
                        subject=subject,
                        html_content=html_content,
                        text_content=text_content,
                    ),
                    timeout=10.0
                )
                
                if 200 <= response.status_code < 300:
                    logger.info(f"Email sent successfully to {to_email}: {subject} (from={resend_from})")
                    return True
                else:
                    logger.error(
                        f"Failed to send email via Resend: {response.status_code} - {response.text} "
                        f"(to={to_email}, from={resend_from}, subject={subject})"
                    )
                    return False
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

    @staticmethod
    def _build_resend_payload(
        resend_from: str,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str],
    ) -> Dict:
        payload: Dict = {
            "from": resend_from,
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        }
        if text_content:
            payload["text"] = text_content
        return payload
    
    def generate_share_token(self) -> str:
        """Generate a unique share token"""
        return secrets.token_urlsafe(16)


# Helper function for dependency injection
async def get_notification_service(db: AsyncSession = None) -> NotificationService:
    """Get notification service instance."""
    return NotificationService(db)

