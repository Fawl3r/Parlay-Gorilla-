"""Notification service for email and in-app notifications"""

from typing import Dict, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
import secrets
import logging

from app.core.config import settings
from app.models.user import User
from app.models.parlay import Parlay

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
        subject = "Verify your Parlay Gorilla account"
        
        html_content = self._get_email_verification_template(
            user_name=user.display_name or user.username or user.email.split('@')[0],
            verification_url=verification_url
        )
        
        return await self.send_email(user.email, subject, html_content)
    
    def _get_email_verification_template(
        self,
        user_name: str,
        verification_url: str
    ) -> str:
        """Generate email verification HTML template."""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Your Email</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #0a0a0f;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0a0a0f; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="max-width: 600px; background-color: #111118; border-radius: 16px; border: 1px solid rgba(16, 185, 129, 0.2);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 20px; text-align: center;">
                            <h1 style="margin: 0; font-size: 32px; font-weight: bold; color: #ffffff;">
                                🦍 Parlay Gorilla
                            </h1>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 20px 40px;">
                            <h2 style="margin: 0 0 20px; font-size: 24px; color: #ffffff;">
                                Hey {user_name}! 👋
                            </h2>
                            <p style="margin: 0 0 20px; font-size: 16px; line-height: 1.6; color: #a1a1aa;">
                                Welcome to Parlay Gorilla! Please verify your email address to get started with AI-powered parlay generation.
                            </p>
                            <p style="margin: 0 0 30px; font-size: 16px; line-height: 1.6; color: #a1a1aa;">
                                Click the button below to verify your email:
                            </p>
                            
                            <!-- CTA Button -->
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="center">
                                        <a href="{verification_url}" style="display: inline-block; padding: 16px 32px; font-size: 16px; font-weight: bold; color: #000000; background: linear-gradient(to right, #10b981, #22c55e); text-decoration: none; border-radius: 8px;">
                                            Verify Email Address
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="margin: 30px 0 0; font-size: 14px; line-height: 1.6; color: #71717a;">
                                If the button doesn't work, copy and paste this link into your browser:
                            </p>
                            <p style="margin: 10px 0 0; font-size: 12px; word-break: break-all; color: #10b981;">
                                {verification_url}
                            </p>
                            
                            <p style="margin: 30px 0 0; font-size: 14px; line-height: 1.6; color: #71717a;">
                                This link expires in 48 hours.
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px 40px; border-top: 1px solid rgba(255, 255, 255, 0.1);">
                            <p style="margin: 0; font-size: 12px; color: #71717a; text-align: center;">
                                If you didn't create an account with Parlay Gorilla, you can safely ignore this email.
                            </p>
                            <p style="margin: 10px 0 0; font-size: 12px; color: #71717a; text-align: center;">
                                © {datetime.now().year} Parlay Gorilla. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    
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
        subject = "Reset your Parlay Gorilla password"
        
        html_content = self._get_password_reset_template(
            user_name=user.display_name or user.username or user.email.split('@')[0],
            reset_url=reset_url
        )
        
        return await self.send_email(user.email, subject, html_content)
    
    def _get_password_reset_template(
        self,
        user_name: str,
        reset_url: str
    ) -> str:
        """Generate password reset HTML template."""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reset Your Password</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #0a0a0f;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0a0a0f; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="max-width: 600px; background-color: #111118; border-radius: 16px; border: 1px solid rgba(16, 185, 129, 0.2);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 20px; text-align: center;">
                            <h1 style="margin: 0; font-size: 32px; font-weight: bold; color: #ffffff;">
                                🦍 Parlay Gorilla
                            </h1>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 20px 40px;">
                            <h2 style="margin: 0 0 20px; font-size: 24px; color: #ffffff;">
                                Password Reset Request
                            </h2>
                            <p style="margin: 0 0 20px; font-size: 16px; line-height: 1.6; color: #a1a1aa;">
                                Hey {user_name}, we received a request to reset your password. Click the button below to create a new password:
                            </p>
                            
                            <!-- CTA Button -->
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="center">
                                        <a href="{reset_url}" style="display: inline-block; padding: 16px 32px; font-size: 16px; font-weight: bold; color: #000000; background: linear-gradient(to right, #10b981, #22c55e); text-decoration: none; border-radius: 8px;">
                                            Reset Password
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="margin: 30px 0 0; font-size: 14px; line-height: 1.6; color: #71717a;">
                                If the button doesn't work, copy and paste this link into your browser:
                            </p>
                            <p style="margin: 10px 0 0; font-size: 12px; word-break: break-all; color: #10b981;">
                                {reset_url}
                            </p>
                            
                            <div style="margin: 30px 0; padding: 16px; background-color: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px;">
                                <p style="margin: 0; font-size: 14px; color: #f87171;">
                                    ⚠️ This link expires in 2 hours for security reasons.
                                </p>
                            </div>
                            
                            <p style="margin: 0; font-size: 14px; line-height: 1.6; color: #71717a;">
                                If you didn't request this password reset, please ignore this email or contact support if you have concerns.
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px 40px; border-top: 1px solid rgba(255, 255, 255, 0.1);">
                            <p style="margin: 0; font-size: 12px; color: #71717a; text-align: center;">
                                This is an automated email from Parlay Gorilla. Please do not reply.
                            </p>
                            <p style="margin: 10px 0 0; font-size: 12px; color: #71717a; text-align: center;">
                                © {datetime.now().year} Parlay Gorilla. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    
    # =========================================================================
    # Generic Email Sending
    # =========================================================================
    
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
            # Log warning that email cannot be sent
            logger.warning(
                f"⚠️  EMAIL NOT SENT: RESEND_API_KEY not configured. "
                f"Would send to {to_email}: {subject}"
            )
            logger.warning(
                "To enable email sending, set RESEND_API_KEY in your environment variables. "
                "Get a free API key at https://resend.com"
            )
            # Still return True so the flow continues, but log clearly
            return True  # Return True so flows continue, but user should know email wasn't sent
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {resend_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "from": "Parlay Gorilla <noreply@parlaygorilla.com>",
                        "to": [to_email],
                        "subject": subject,
                        "html": html_content
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info(f"Email sent successfully to {to_email}: {subject}")
                    return True
                else:
                    logger.error(f"Failed to send email: {response.status_code} - {response.text}")
                    return False
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    def generate_share_token(self) -> str:
        """Generate a unique share token"""
        return secrets.token_urlsafe(16)


# Helper function for dependency injection
async def get_notification_service(db: AsyncSession = None) -> NotificationService:
    """Get notification service instance."""
    return NotificationService(db)

