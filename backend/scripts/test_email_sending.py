"""
Test script to verify email sending is working.

Run with:
    cd backend
    python scripts/test_email_sending.py your@email.com
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.services.notification_service import NotificationService
from app.models.user import User
from datetime import datetime, timezone
import uuid


async def test_email_sending(test_email: str):
    """Test sending a verification email."""
    print("=" * 60)
    print("Testing Email Sending Configuration")
    print("=" * 60)
    
    # Check configuration
    print(f"\n📋 Configuration Check:")
    print(f"  RESEND_API_KEY set: {bool(settings.resend_api_key)}")
    if settings.resend_api_key:
        print(f"  RESEND_API_KEY (first 10 chars): {settings.resend_api_key[:10]}...")
    print(f"  RESEND_FROM: {settings.resend_from}")
    print(f"  APP_URL: {settings.app_url}")
    
    if not settings.resend_api_key:
        print("\n❌ ERROR: RESEND_API_KEY is not configured!")
        print("   Add RESEND_API_KEY to your .env file")
        print("   Get a free API key at: https://resend.com")
        return False
    
    # Create a test user
    test_user = User(
        id=uuid.uuid4(),
        email=test_email,
        username=test_email.split("@")[0],
        account_number="TEST001",
        email_verified=False,
        created_at=datetime.now(timezone.utc),
    )
    
    # Test sending verification email
    print(f"\n📧 Sending test verification email to: {test_email}")
    notification_service = NotificationService()
    
    verification_url = f"{settings.app_url}/auth/verify-email?token=test_token_12345"
    
    try:
        email_sent = await notification_service.send_email_verification(
            test_user,
            verification_url
        )
        
        if email_sent:
            print("✅ Email sent successfully!")
            print(f"   Check your inbox at: {test_email}")
            print(f"   (Also check spam folder)")
            return True
        else:
            print("❌ Email sending failed!")
            print("   Check backend logs for error details")
            return False
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_email_sending.py your@email.com")
        sys.exit(1)
    
    test_email = sys.argv[1]
    success = asyncio.run(test_email_sending(test_email))
    sys.exit(0 if success else 1)


