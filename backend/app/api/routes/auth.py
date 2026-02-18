"""Authentication routes - JWT-based auth (Render/PostgreSQL)"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import timedelta
import logging
import asyncio

from app.core.dependencies import get_db, get_current_user
from app.core.config import settings
from app.middleware.rate_limiter import rate_limit
from app.services.auth import AuthCookieManager, EmailNormalizer
from app.services.auth_service import (
    authenticate_user,
    create_user,
    create_access_token,
    decode_access_token,
    ACCESS_TOKEN_EXPIRE_HOURS,
)
from app.services.verification_service import VerificationService
from app.services.notification_service import NotificationService
from app.services.badge_service import BadgeService
from app.services.affiliate_cookie_attribution_service import AffiliateCookieAttributionService
from app.models.user import User
from sqlalchemy import select
from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()


# ============================================================================
# Request/Response Schemas
# ============================================================================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=200, description="Password must be 6-200 characters")


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=200, description="Password must be 6-200 characters")
    username: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class UserProfileResponse(BaseModel):
    """User profile response schema"""
    id: str
    email: str
    account_number: str
    username: Optional[str]
    display_name: Optional[str]
    avatar_url: Optional[str]
    bio: Optional[str]
    timezone: Optional[str]
    email_verified: bool
    profile_completed: bool
    default_risk_profile: str
    favorite_teams: list
    favorite_sports: list
    created_at: str
    last_login: Optional[str]
    
    model_config = {"from_attributes": True}


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(..., min_length=6, max_length=200, description="Password must be 6-200 characters")


class VerifyEmailRequest(BaseModel):
    token: str


class MessageResponse(BaseModel):
    message: str


# ============================================================================
# Login/Register Endpoints
# ============================================================================

@router.post("/login", response_model=TokenResponse)
@rate_limit("10/minute")  # 10 login attempts per minute per IP to prevent brute force
async def login(
    request: Request,
    login_data: LoginRequest,
    http_response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Login and get JWT token"""
    try:
        # Normalize inputs at the boundary (defense-in-depth).
        normalized_email = EmailNormalizer().normalize(str(login_data.email))
        user = await asyncio.wait_for(
            authenticate_user(db, normalized_email, login_data.password),
            timeout=5.0
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Create access token
        user_id = str(user.id)
        access_token = create_access_token(
            data={"sub": user_id, "email": user.email}
        )

        # Best-effort affiliate attribution from cookies.
        await AffiliateCookieAttributionService(db).attribute_user_if_present(
            user=user, request=request, response=http_response
        )

        # Hybrid auth: also set HttpOnly cookie (in addition to JSON response).
        AuthCookieManager().set_access_token_cookie(http_response, access_token)
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_HOURS * 3600,
            user={
                "id": user_id,
                "email": user.email,
                "account_number": user.account_number,
                "username": getattr(user, 'username', None),
                "email_verified": getattr(user, 'email_verified', False),
                "profile_completed": getattr(user, 'profile_completed', False),
            }
        )
    except asyncio.TimeoutError:
        logger.error("Login timeout exceeded")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Authentication request timed out. Please try again."
        )
    except HTTPException:
        # Preserve intended status codes (e.g., 401 invalid credentials).
        raise
    except OperationalError as e:
        logger.error("Login failed: database unavailable: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable. Ensure Postgres is running and DATABASE_URL is set (e.g. localhost for local dev).",
        )
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )


@router.post("/register", response_model=TokenResponse)
@rate_limit("5/minute")  # 5 registrations per minute per IP to prevent abuse
async def register(
    request: Request,
    register_data: RegisterRequest,
    http_response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user and get JWT token"""
    # #region agent log
    import json
    log_path = r"c:\F3 Apps\F3 Parlay Gorilla\.cursor\debug.log"
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"auth.py:169","message":"Register endpoint entry","data":{"email":str(register_data.email)[:10]+"...","hasUsername":bool(register_data.username)},"timestamp":int(__import__("time").time()*1000)})+"\n")
    except: pass
    # #endregion
    try:
        # Normalize inputs at the boundary (defense-in-depth).
        normalized_email = EmailNormalizer().normalize(str(register_data.email))
        # #region agent log
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"auth.py:179","message":"Before create_user","data":{"normalizedEmail":normalized_email[:10]+"..."},"timestamp":int(__import__("time").time()*1000)})+"\n")
        except: pass
        # #endregion
        user = await asyncio.wait_for(
            create_user(
                db,
                email=normalized_email,
                password=register_data.password,
                username=register_data.username
            ),
            timeout=10.0
        )
        # #region agent log
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"auth.py:187","message":"After create_user","data":{"userId":str(user.id),"accountNumber":user.account_number},"timestamp":int(__import__("time").time()*1000)})+"\n")
        except: pass
        # #endregion
        
        # Create access token
        user_id = str(user.id)
        access_token = create_access_token(
            data={"sub": user_id, "email": user.email}
        )

        # Best-effort affiliate attribution from cookies.
        await AffiliateCookieAttributionService(db).attribute_user_if_present(
            user=user, request=request, response=http_response
        )

        # Hybrid auth: also set HttpOnly cookie (in addition to JSON response).
        AuthCookieManager().set_access_token_cookie(http_response, access_token)
        
        # Send verification email (async, don't block registration)
        try:
            verification_service = VerificationService(db)
            notification_service = NotificationService()

            _, raw_token = await verification_service.create_email_verification_token(user_id)
            verification_url = f"{settings.app_url}/auth/verify-email?token={raw_token}"
            email_sent = await notification_service.send_email_verification(user, verification_url)
            if not email_sent:
                logger.warning(
                    "Verification email was not sent (email provider misconfigured or rejected the message). "
                    "Check RESEND_API_KEY / RESEND_FROM and Resend domain verification. "
                    f"(user={user.email})"
                )
        except Exception as e:
            # Log but don't fail registration
            logger.warning(f"Failed to send verification email: {e}")
        
        # #region agent log
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"auth.py:241","message":"Register success","data":{"userId":user_id,"profileCompleted":getattr(user, 'profile_completed', False)},"timestamp":int(__import__("time").time()*1000)})+"\n")
        except: pass
        # #endregion
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_HOURS * 3600,
            user={
                "id": user_id,
                "email": user.email,
                "account_number": user.account_number,
                "username": getattr(user, 'username', None),
                "email_verified": getattr(user, 'email_verified', False),
                "profile_completed": getattr(user, 'profile_completed', False),
            }
        )
    except asyncio.TimeoutError:
        logger.error("Registration timeout exceeded")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Registration request timed out. Please try again."
        )
    except HTTPException:
        # Preserve intended status codes (e.g., 400 user exists).
        raise
    except ValueError as e:
        error_msg = str(e)
        # Log the actual error for debugging
        logger.error(f"Registration ValueError: {error_msg}")
        # Provide user-friendly error messages for common validation errors
        # Only sanitize if it's actually a bcrypt 72-byte error (more specific check)
        if "72" in error_msg and "byte" in error_msg.lower() and ("bcrypt" in error_msg.lower() or "password" in error_msg.lower() and "cannot" in error_msg.lower()):
            error_msg = "Password is too long. Please use a password with 72 characters or fewer."
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    except Exception as e:
        import traceback
        error_detail = str(e)
        traceback.print_exc()
        logger.error(f"Registration error: {error_detail}")
        
        # Sanitize error messages for user-facing responses
        user_friendly_detail = error_detail
        # Only sanitize if it's actually a bcrypt 72-byte error (more specific check)
        if "72" in error_detail and "byte" in error_detail.lower() and ("bcrypt" in error_detail.lower() or ("password" in error_detail.lower() and "cannot" in error_detail.lower() and "truncate" in error_detail.lower())):
            user_friendly_detail = "Password is too long. Please use a password with 72 characters or fewer."
        elif "password" in error_detail.lower() and "cannot" in error_detail.lower():
            user_friendly_detail = "Invalid password. Please check your password and try again."
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {user_friendly_detail}"
        )


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's profile"""
    return UserProfileResponse(
        id=str(user.id),
        email=user.email,
        account_number=user.account_number,
        username=user.username,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        bio=user.bio,
        timezone=user.timezone,
        email_verified=user.email_verified,
        profile_completed=user.profile_completed,
        default_risk_profile=user.default_risk_profile,
        favorite_teams=user.favorite_teams or [],
        favorite_sports=user.favorite_sports or [],
        created_at=user.created_at.isoformat() if user.created_at else "",
        last_login=user.last_login.isoformat() if user.last_login else None,
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(http_response: Response):
    """Clear auth cookies (hybrid auth)."""
    AuthCookieManager().clear_access_token_cookie(http_response)
    return MessageResponse(message="Logged out")


# ============================================================================
# Email Verification Endpoints
# ============================================================================

@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    verify_data: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify email address using token from email.
    
    On success:
    - Marks user.email_verified = True
    - Awards "Verified Gorilla" badge
    """
    verification_service = VerificationService(db)
    
    user = await verification_service.verify_email_token(verify_data.token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Award verification badge
    try:
        badge_service = BadgeService(db)
        await badge_service.award_badge_by_slug(str(user.id), "verified-gorilla")
    except Exception as e:
        logger.warning(f"Failed to award verification badge: {e}")
    
    return MessageResponse(message="Email verified successfully")


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification_email(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Resend verification email to current user.
    
    Requires authentication.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.email_verified:
        return MessageResponse(message="Email already verified")
    
    # Create and send new verification token
    verification_service = VerificationService(db)
    notification_service = NotificationService()
    
    _, raw_token = await verification_service.create_email_verification_token(str(user.id))
    verification_url = f"{settings.app_url}/auth/verify-email?token={raw_token}"
    
    email_sent = await notification_service.send_email_verification(user, verification_url)
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to send verification email right now. Please try again later."
        )
    
    return MessageResponse(message="Verification email sent")


# ============================================================================
# Password Reset Endpoints
# ============================================================================

@router.post("/forgot-password", response_model=MessageResponse)
@rate_limit("5/hour")  # 5 password reset requests per hour per IP to prevent abuse
async def forgot_password(
    request: Request,
    forgot_data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Request password reset email.
    
    Always returns success (prevents email enumeration).
    """
    _ = request
    verification_service = VerificationService(db)
    notification_service = NotificationService()
    
    # Find user
    normalized_email = EmailNormalizer().normalize(str(forgot_data.email))
    user = await verification_service.get_user_by_email(normalized_email)
    
    if user:
        # Create and send reset token
        _, raw_token = await verification_service.create_password_reset_token(str(user.id))
        reset_url = f"{settings.app_url}/auth/reset-password?token={raw_token}"
        
        email_sent = await notification_service.send_password_reset(user, reset_url)
        
        if email_sent:
            # Check if Resend API key is configured (email might not actually be sent)
            if not settings.resend_api_key:
                logger.warning(
                    f"⚠️  Password reset requested for {forgot_data.email} but RESEND_API_KEY not configured. "
                    f"Email was NOT sent. Reset token: {reset_url[:50]}..."
                )
            else:
                logger.info(f"Password reset email sent to {forgot_data.email}")
        else:
            logger.warning(f"Failed to send password reset email to {forgot_data.email}")
    else:
        # Don't reveal if email exists
        logger.info(f"Password reset requested for non-existent email: {forgot_data.email}")
    
    # Always return success to prevent email enumeration
    return MessageResponse(message="If an account with that email exists, a password reset link has been sent")


@router.post("/reset-password", response_model=MessageResponse)
@rate_limit("10/hour")  # 10 password reset attempts per hour per IP
async def reset_password(
    request: Request,
    reset_data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Reset password using token from email.
    """
    _ = request
    verification_service = VerificationService(db)
    
    user = await verification_service.reset_password(reset_data.token, reset_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    return MessageResponse(message="Password reset successfully")
