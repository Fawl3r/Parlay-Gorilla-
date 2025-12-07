# Authentication & Authorization Setup

## Overview

Parlay Gorilla uses a custom JWT-based authentication system with:
- **Backend**: FastAPI + python-jose (JWT) + passlib (bcrypt)
- **Frontend**: Next.js App Router + React Context
- **Billing**: LemonSqueezy (card payments) + Coinbase Commerce (crypto)
- **Email**: Resend API (for transactional emails)

---

## Current Auth Flow

### Registration Flow
```
User -> Frontend (SignupPage) -> POST /api/auth/register
                                        |
                                        v
                              auth_service.create_user()
                                        |
                                        v
                              - Check email uniqueness
                              - Hash password (bcrypt)
                              - Create User record
                              - Generate JWT token
                                        |
                                        v
                              Return TokenResponse { access_token, user }
                                        |
                                        v
Frontend stores token in localStorage('auth_token')
                                        |
                                        v
                              Redirect to /app
```

### Login Flow
```
User -> Frontend (LoginPage) -> POST /api/auth/login
                                        |
                                        v
                              auth_service.authenticate_user()
                                        |
                                        v
                              - Find user by email
                              - Verify password hash
                              - Update last_login timestamp
                              - Generate JWT token
                                        |
                                        v
                              Return TokenResponse { access_token, user }
                                        |
                                        v
Frontend stores token in localStorage('auth_token')
                                        |
                                        v
                              Redirect to /app (or saved redirect)
```

### Token Verification Flow
```
Frontend Request -> Authorization: Bearer <token>
                                        |
                                        v
                              get_current_user dependency
                                        |
                                        v
                              decode_access_token(token)
                                        |
                                        v
                              - Verify JWT signature (jwt_secret)
                              - Check expiration
                              - Extract user_id from 'sub' claim
                                        |
                                        v
                              Query User by ID
                                        |
                                        v
                              Return User object
```

---

## Key Files

### Backend

| File | Purpose |
|------|---------|
| `app/models/user.py` | User model with profile fields |
| `app/services/auth_service.py` | Password hashing, JWT creation/verification |
| `app/api/routes/auth.py` | Login, Register, /me endpoints |
| `app/core/dependencies.py` | `get_current_user` dependency |
| `app/core/config.py` | JWT settings (secret, algorithm, expiration) |

### Frontend

| File | Purpose |
|------|---------|
| `lib/auth-context.tsx` | React Context for auth state |
| `lib/api.ts` | API client with auth interceptor |
| `app/auth/login/page.tsx` | Login page |
| `app/auth/signup/page.tsx` | Registration page |

---

## Current User Model Fields

```python
class User(Base):
    id = Column(GUID())
    email = Column(String, unique=True)
    username = Column(String, nullable=True)
    password_hash = Column(String)
    
    # Role and access
    role = Column(String, default="user")  # user, mod, admin
    plan = Column(String, default="free")  # free, standard, elite
    is_active = Column(Boolean, default=True)
    
    # Profile
    display_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    default_risk_profile = Column(String, default="balanced")
    favorite_teams = Column(JSON, default=list)
    favorite_sports = Column(JSON, default=list)
    
    # Timestamps
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    last_login = Column(DateTime, nullable=True)
```

### Missing Fields (To Be Added)
- `email_verified: Boolean = False`
- `profile_completed: Boolean = False`
- `bio: Text (nullable)`
- `timezone: String (nullable)`

---

## JWT Configuration

```python
# app/core/config.py
jwt_secret: str = "your-super-secret-key"
jwt_algorithm: str = "HS256"
jwt_expiration_hours: int = 24
```

JWT Payload:
```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "exp": 1234567890
}
```

---

## Integration Points for New Features

### 1. Email Verification

**Where to plug in:**
- After `create_user()` in `auth_service.py`:
  1. Generate verification token
  2. Store token hash in new `VerificationToken` table
  3. Send email via `NotificationService.send_email_verification()`

- New endpoints in `auth.py`:
  - `POST /api/auth/verify-email` - Verify token
  - `POST /api/auth/resend-verification` - Resend email

**Frontend:**
- Show `VerificationBanner` if `user.email_verified === false`
- Create `/auth/verify-email?token=xxx` page

### 2. Password Reset

**Where to plug in:**
- New endpoints in `auth.py`:
  - `POST /api/auth/forgot-password` - Request reset
  - `POST /api/auth/reset-password` - Execute reset

- Reuse `VerificationToken` model with `token_type="password_reset"`

**Frontend:**
- Add "Forgot password?" link to login page
- Create `/auth/forgot-password` page
- Create `/auth/reset-password?token=xxx` page

### 3. Profile System

**Where to plug in:**
- New `ProfileService` for profile operations
- New `/api/profile` routes:
  - `GET /api/profile/me` - Get profile + stats + badges
  - `PUT /api/profile/me` - Update profile
  - `POST /api/profile/setup` - Complete initial setup

**Frontend:**
- If `!profile_completed` after signup -> redirect to `/profile/setup`
- Create profile setup wizard (multi-step form)
- Create `/profile` page

### 4. Badge System

**Where to plug in:**
- After parlay saved in `parlay.py`:
  1. Call `BadgeService.check_and_award_badges(user_id)`
  2. Include `newly_unlocked_badges` in response

**Models:**
- `Badge` - Badge definitions
- `UserBadge` - User's earned badges

---

## Billing Integration

### Current Setup

**Providers:**
- LemonSqueezy (card payments, recurring subscriptions)
- Coinbase Commerce (crypto payments, lifetime access)

**Key Files:**
- `app/api/routes/billing.py` - Checkout endpoints
- `app/api/routes/webhooks.py` - Payment webhooks
- `app/models/subscription.py` - Subscription tracking
- `app/models/payment.py` - Payment records
- `app/services/subscription_service.py` - Access level checks

### Subscription Flow
```
User -> GET /api/billing/plans -> Display pricing page
User -> POST /api/billing/lemonsqueezy/checkout OR /coinbase/checkout
                                        |
                                        v
                              Create checkout session
                              Return hosted checkout URL
                                        |
                                        v
User completes payment on provider's hosted page
                                        |
                                        v
Provider sends webhook -> POST /api/webhooks/lemonsqueezy or /coinbase
                                        |
                                        v
                              - Verify webhook signature
                              - Create/update Subscription record
                              - Update User.plan
```

### Where to Add Subscription Center

**New endpoints (in `billing.py` or new `subscription.py`):**
- `GET /api/subscription/me` - Current subscription state
- `GET /api/subscription/history` - Payment history
- `POST /api/subscription/cancel` - Request cancellation

**Frontend:**
- Add `SubscriptionPanel` component to `/profile` page
- Show: plan name, status, renewal date, cancel button
- Show: billing history table

---

## Auth Response Update (CRITICAL)

Current login/register responses:
```json
{
  "access_token": "...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "optional"
  }
}
```

**After implementation, add:**
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "optional",
    "email_verified": false,    // NEW
    "profile_completed": false  // NEW
  }
}
```

Frontend `auth-context.tsx` must parse and store these fields for:
- Redirect to `/profile/setup` if `!profile_completed`
- Show verification banner if `!email_verified`

---

## Security Considerations

### Token Storage
- **Current**: SHA-256 hash of raw tokens stored in DB
- **Verification tokens**: Store `token_hash`, return raw token to user
- **Password reset tokens**: Same approach, short expiration (1-24 hours)

### Rate Limiting
- Existing `slowapi` rate limiting on parlay endpoints
- Add rate limiting to:
  - `/api/auth/forgot-password` (prevent email spam)
  - `/api/auth/resend-verification` (prevent email spam)

### Guards
- Consider blocking subscription purchases if `email_verified == False`
- Consider soft-blocking advanced features if `profile_completed == False`

---

## Implementation Status ✅

All features have been implemented:

### Backend
- ✅ User model extended with `email_verified`, `profile_completed`, `bio`, `timezone`
- ✅ `VerificationToken`, `Badge`, `UserBadge` models created
- ✅ Alembic migration `004_add_profile_badges_verification.py`
- ✅ `ProfileService` - Profile retrieval, updates, stats, all badges
- ✅ `BadgeService` - Badge checking and awarding with race condition handling
- ✅ `VerificationService` - Secure token generation and verification
- ✅ Profile routes: `GET/PUT /api/profile/me`, `POST /api/profile/setup`
- ✅ Auth routes: verify-email, resend-verification, forgot/reset-password
- ✅ Subscription routes: `GET /api/subscription/me`, `/history`, `POST /cancel`
- ✅ Badge awarding integrated into parlay generation
- ✅ Expired token cleanup scheduled task
- ✅ Email templates for verification and password reset

### Frontend
- ✅ Auth context updated with `email_verified` and `profile_completed`
- ✅ Profile setup wizard with multi-step flow
- ✅ Profile page with header, stats, badges, subscription sections
- ✅ ProfileHeader, ProfileStats, BadgeGrid, BadgeCard components
- ✅ SubscriptionPanel and BillingHistory components
- ✅ BadgeUnlockModal with confetti animation
- ✅ VerificationBanner for unverified users
- ✅ Forgot password, reset password, verify email pages
- ✅ Page transition animations
- ✅ Header updated with Profile link

## File Locations

### Backend New Files
- `app/models/verification_token.py` - Secure verification tokens
- `app/models/badge.py` - Badge definitions with starter badges
- `app/models/user_badge.py` - User badge tracking
- `app/services/profile_service.py` - Profile operations
- `app/services/badge_service.py` - Badge awarding logic
- `app/services/verification_service.py` - Token management
- `app/api/routes/profile.py` - Profile API endpoints
- `app/api/routes/subscription.py` - Subscription API endpoints
- `alembic/versions/004_add_profile_badges_verification.py` - Migration
- `scripts/seed_badges.py` - Badge seeding script
- `tests/test_profile_verification_badges.py` - Unit tests

### Backend Modified Files
- `app/models/user.py` - Added new fields
- `app/models/__init__.py` - Export new models
- `app/api/routes/auth.py` - Added verification endpoints
- `app/api/routes/parlay.py` - Badge awarding integration
- `app/schemas/parlay.py` - Added BadgeInfo schema
- `app/services/notification_service.py` - Email templates
- `app/services/scheduler.py` - Token cleanup task
- `app/main.py` - Register new routers

### Frontend New Files
- `app/profile/page.tsx` - Profile page
- `app/profile/setup/page.tsx` - Profile setup wizard
- `app/auth/forgot-password/page.tsx` - Forgot password
- `app/auth/reset-password/page.tsx` - Reset password
- `app/auth/verify-email/page.tsx` - Email verification
- `app/template.tsx` - Page transitions
- `components/profile/ProfileHeader.tsx`
- `components/profile/ProfileStats.tsx`
- `components/profile/BadgeCard.tsx`
- `components/profile/BadgeGrid.tsx`
- `components/profile/SubscriptionPanel.tsx`
- `components/profile/BillingHistory.tsx`
- `components/VerificationBanner.tsx`
- `components/BadgeUnlockModal.tsx`

### Frontend Modified Files
- `lib/api.ts` - Added all new API methods and types
- `lib/auth-context.tsx` - Added verification/profile flags
- `components/Header.tsx` - Added Profile link
- `app/auth/login/page.tsx` - Added forgot password link

## Running the System

### Apply Migration
```bash
cd backend
alembic upgrade head
```

### Seed Badges
```bash
cd backend
python scripts/seed_badges.py
```

### Run Tests
```bash
cd backend
pytest tests/test_profile_verification_badges.py -v
```

## API Endpoints Summary

### Profile
- `GET /api/profile/me` - Get profile with stats and badges
- `PUT /api/profile/me` - Update profile fields
- `POST /api/profile/setup` - Complete initial setup

### Auth (Extended)
- `POST /api/auth/verify-email` - Verify email with token
- `POST /api/auth/resend-verification` - Resend verification email
- `POST /api/auth/forgot-password` - Request password reset
- `POST /api/auth/reset-password` - Reset password with token

### Subscription
- `GET /api/subscription/me` - Current subscription state
- `GET /api/subscription/history` - Payment history
- `POST /api/subscription/cancel` - Cancel subscription

