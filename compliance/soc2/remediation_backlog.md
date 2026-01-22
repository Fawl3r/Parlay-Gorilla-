# Remediation Backlog

**Product:** Parlay Gorilla  
**Last Updated:** 2025-01-XX  
**Status:** Pre-Audit Readiness

---

## Priority Levels

**P0 (Must Fix Before Audit):** Critical security gaps that must be addressed before SOC 2 Type I audit  
**P1 (Should Fix):** Important improvements that should be implemented  
**P2 (Improvement/Maturity):** Enhancements for security maturity and best practices

---

## P0 - Must Fix Before Audit

### REM-001: Implement JWT Refresh Token Mechanism

**Risk:** R-002  
**Control:** CC6.2.5  
**Description:** Currently, JWT tokens expire after 24 hours with no refresh mechanism. Users must re-authenticate after expiration.

**Risk Addressed:**
- Improved user experience (no forced re-authentication)
- Better security (shorter-lived access tokens)
- Token revocation capability

**Files to Modify:**
- `backend/app/services/auth_service.py` - Add refresh token generation
- `backend/app/api/routes/auth.py` - Add `/api/auth/refresh` endpoint
- `backend/app/models/user.py` - Add `refresh_token` field (optional, or store in separate table)
- `frontend/lib/auth-context.tsx` - Add refresh token logic

**Example Code:**
```python
# backend/app/services/auth_service.py
def create_refresh_token(user_id: str) -> str:
    """Create a long-lived refresh token"""
    data = {"sub": user_id, "type": "refresh"}
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    return jwt.encode(
        {"sub": user_id, "type": "refresh", "exp": expire},
        settings.jwt_secret,
        algorithm=ALGORITHM
    )

# backend/app/api/routes/auth.py
@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token"""
    payload = decode_access_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(401, "Invalid refresh token")
    
    user_id = payload.get("sub")
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(401, "User not found")
    
    new_access_token = create_access_token(data={"sub": user_id})
    return {"access_token": new_access_token}
```

**Audit Evidence:**
- Code review showing refresh token implementation
- Test results for refresh token flow
- Documentation of refresh token expiration (7 days)

**Estimated Effort:** 4-6 hours

---

### REM-002: Implement Admin Action Logging

**Risk:** R-007  
**Control:** CC7.2.3  
**Description:** Admin actions (user management, payment reconciliation, etc.) are not currently logged.

**Risk Addressed:**
- Audit trail for admin actions
- Detection of unauthorized admin activity
- Compliance with SOC 2 monitoring requirements

**Files to Modify:**
- `backend/app/models/admin_action_log.py` - New model for admin actions
- `backend/app/services/admin_audit_service.py` - New service for logging admin actions
- `backend/app/api/routes/admin/*.py` - Add audit logging to admin endpoints
- `backend/alembic/versions/XXX_add_admin_action_log.py` - Database migration

**Example Code:**
```python
# backend/app/models/admin_action_log.py
class AdminActionLog(Base):
    __tablename__ = "admin_action_logs"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    admin_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    action = Column(String(100), nullable=False)  # e.g., "update_user", "process_payout"
    resource_type = Column(String(50), nullable=True)  # e.g., "user", "payment"
    resource_id = Column(String(100), nullable=True)
    details = Column(JSON, nullable=True)  # Action-specific details
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

# backend/app/services/admin_audit_service.py
class AdminAuditService:
    async def log_action(
        self,
        db: AsyncSession,
        admin: User,
        action: str,
        resource_type: str = None,
        resource_id: str = None,
        details: dict = None,
        request: Request = None
    ):
        log = AdminActionLog(
            admin_id=admin.id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None
        )
        db.add(log)
        await db.commit()
```

**Audit Evidence:**
- Database schema showing admin_action_logs table
- Code review showing audit logging in admin endpoints
- Sample admin action log entries
- Documentation of logged actions

**Estimated Effort:** 6-8 hours

---

### REM-003: Implement Security Event Logging

**Risk:** R-006  
**Control:** CC7.1.3, CC7.3.1, CC7.3.2  
**Description:** Security events (failed logins, unauthorized access attempts) are not comprehensively logged.

**Risk Addressed:**
- Detection of brute force attacks
- Detection of unauthorized access attempts
- Compliance with SOC 2 monitoring requirements

**Files to Modify:**
- `backend/app/models/security_event_log.py` - New model for security events
- `backend/app/services/security_event_service.py` - New service for logging security events
- `backend/app/api/routes/auth.py` - Log failed login attempts
- `backend/app/core/dependencies.py` - Log unauthorized access attempts
- `backend/alembic/versions/XXX_add_security_event_log.py` - Database migration

**Example Code:**
```python
# backend/app/models/security_event_log.py
class SecurityEventType(str, enum.Enum):
    FAILED_LOGIN = "failed_login"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    TOKEN_VALIDATION_FAILED = "token_validation_failed"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    ADMIN_ACTION_DENIED = "admin_action_denied"

class SecurityEventLog(Base):
    __tablename__ = "security_event_logs"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(50), nullable=False, index=True)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=True)
    ip_address = Column(String(45), nullable=True, index=True)
    user_agent = Column(String(255), nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

# backend/app/api/routes/auth.py
@router.post("/login")
async def login(...):
    try:
        user = await authenticate_user(...)
        if not user:
            # Log failed login attempt
            await security_event_service.log_event(
                db,
                SecurityEventType.FAILED_LOGIN,
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent"),
                details={"email": login_data.email}
            )
            raise HTTPException(401, "Incorrect email or password")
        # ... rest of login logic
```

**Audit Evidence:**
- Database schema showing security_event_logs table
- Code review showing security event logging
- Sample security event log entries
- Documentation of logged event types

**Estimated Effort:** 6-8 hours

---

### REM-004: Enable MFA for Infrastructure Access

**Risk:** R-004  
**Control:** CC6.1.5  
**Description:** Multi-factor authentication (MFA) should be enabled for Render dashboard and GitHub accounts.

**Risk Addressed:**
- Protection against compromised passwords
- Compliance with SOC 2 access control requirements
- Defense-in-depth security

**Files to Modify:**
- None (infrastructure configuration)

**Process:**
1. **Render Dashboard:**
   - Go to Render Dashboard → Account → Security
   - Enable two-factor authentication
   - Use authenticator app (Google Authenticator, Authy, etc.)
   - Save backup codes securely

2. **GitHub:**
   - Go to GitHub → Settings → Security → Two-factor authentication
   - Enable two-factor authentication
   - Use authenticator app or SMS
   - Save backup codes securely

**Audit Evidence:**
- Screenshots of MFA configuration in Render dashboard
- Screenshots of MFA configuration in GitHub
- Documentation of MFA setup date
- Backup codes stored securely (not in evidence)

**Estimated Effort:** 30 minutes

---

### REM-005: Implement Password Policy Enforcement

**Risk:** R-005  
**Control:** CC6.2.8  
**Description:** Password complexity requirements are not currently enforced.

**Risk Addressed:**
- Protection against weak passwords
- Compliance with security best practices
- Reduced risk of password-based attacks

**Files to Modify:**
- `backend/app/api/routes/auth.py` - Add password validation to register and reset_password endpoints
- `backend/app/api/schemas/auth.py` - Add password validation to request models (if using Pydantic)

**Example Code:**
```python
# backend/app/api/routes/auth.py
import re

def validate_password(password: str) -> tuple[bool, str]:
    """Validate password meets complexity requirements"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    return True, ""

@router.post("/register")
async def register(register_data: RegisterRequest, ...):
    is_valid, error_msg = validate_password(register_data.password)
    if not is_valid:
        raise HTTPException(400, detail=error_msg)
    # ... rest of registration logic
```

**Audit Evidence:**
- Code review showing password validation
- Test results for password validation (valid and invalid passwords)
- Documentation of password policy requirements

**Estimated Effort:** 2-3 hours

---

### REM-006: Document Secrets Rotation Process

**Risk:** R-008  
**Control:** CC8.2.4 (enhancement)  
**Description:** Secrets rotation process is not documented or formalized.

**Risk Addressed:**
- Reduced risk of compromised secrets
- Compliance with security best practices
- Clear process for secret management

**Files to Create:**
- `compliance/policies/secrets_management_policy.md` - New policy document

**Process Documentation:**
1. **JWT Secret Rotation:**
   - Generate new JWT_SECRET in Render
   - Update environment variable
   - Restart services
   - All existing tokens will be invalidated (users must re-login)
   - Document rotation date

2. **API Key Rotation:**
   - Generate new API key in vendor dashboard
   - Update environment variable in Render
   - Restart services
   - Verify functionality
   - Document rotation date

3. **Webhook Secret Rotation:**
   - Generate new webhook secret in vendor dashboard
   - Update webhook endpoint in vendor dashboard
   - Update environment variable in Render
   - Restart services
   - Verify webhook functionality
   - Document rotation date

**Rotation Schedule:**
- **JWT_SECRET:** Annually or if compromised
- **API Keys:** Annually or if compromised
- **Webhook Secrets:** Annually or if compromised

**Audit Evidence:**
- Secrets management policy document
- Secrets rotation log (dates, secrets rotated, reason)
- Documentation of rotation procedures

**Estimated Effort:** 2-3 hours (documentation)

---

### REM-007: Implement Backup Verification Process

**Risk:** R-009  
**Control:** CC7.5.2  
**Description:** Database backup restoration is not regularly tested.

**Risk Addressed:**
- Verification of backup integrity
- Confidence in recovery procedures
- Compliance with SOC 2 backup requirements

**Files to Create:**
- `backend/scripts/test_backup_restoration.py` - Backup restoration test script
- `compliance/procedures/backup_verification_procedure.md` - Detailed procedure

**Process:**
1. **Quarterly Backup Test:**
   - Create test database in Render
   - Restore production backup to test database
   - Verify data integrity (sample queries)
   - Verify schema consistency (Alembic version check)
   - Test application connectivity
   - Document test results
   - Clean up test database

**Test Script Example:**
```python
# backend/scripts/test_backup_restoration.py
async def test_backup_restoration():
    """Test database backup restoration"""
    # 1. Create test database
    # 2. Restore backup
    # 3. Verify data integrity
    # 4. Verify schema
    # 5. Test connectivity
    # 6. Document results
    pass
```

**Audit Evidence:**
- Backup verification procedure document
- Backup test results (quarterly)
- Test database creation/deletion logs
- Documentation of test findings

**Estimated Effort:** 4-6 hours (initial setup), 1-2 hours per test

---

### REM-008: Implement Automated Log Retention

**Risk:** R-010  
**Control:** CC7.1.4  
**Description:** Log retention and cleanup is not automated.

**Risk Addressed:**
- Compliance with data retention policy
- Reduced storage costs
- Automated compliance

**Files to Modify:**
- `backend/app/services/log_retention_service.py` - New service for log cleanup
- `backend/app/core/scheduler.py` - Add scheduled job for log cleanup (if using APScheduler)

**Example Code:**
```python
# backend/app/services/log_retention_service.py
from datetime import datetime, timedelta, timezone

async def cleanup_old_logs(db: AsyncSession):
    """Delete logs older than retention period"""
    # Operational logs: 90 days
    operational_cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    # Security logs: 1 year
    security_cutoff = datetime.now(timezone.utc) - timedelta(days=365)
    
    # Delete operational logs (non-security)
    await db.execute(
        delete(SystemLog).where(
            SystemLog.created_at < operational_cutoff,
            SystemLog.level.notin_(["error", "critical"])  # Keep errors longer
        )
    )
    
    # Delete old security events (if security_event_logs table exists)
    # ... security log cleanup
    
    await db.commit()
```

**Audit Evidence:**
- Code review showing log cleanup implementation
- Scheduled job configuration
- Log cleanup execution logs
- Documentation of retention periods

**Estimated Effort:** 4-6 hours

---

## P1 - Should Fix

### REM-101: Implement MFA for Admin Accounts

**Risk:** R-003  
**Control:** CC6.2.7  
**Description:** Multi-factor authentication should be required for admin accounts in the application.

**Implementation:**
- TOTP (Time-based One-Time Password) via authenticator apps
- Store MFA secret in database (encrypted)
- Require MFA on admin login
- Provide backup codes

**Estimated Effort:** 8-12 hours

---

### REM-102: Migrate JWT Storage from localStorage to HttpOnly Cookies

**Risk:** R-001  
**Control:** CC6.2 (enhancement)  
**Description:** Currently using hybrid approach (localStorage + HttpOnly cookies). Migrate to HttpOnly-only for better XSS protection.

**Implementation:**
- Remove localStorage token storage
- Use HttpOnly cookies only
- Update frontend auth context
- Test authentication flow

**Estimated Effort:** 4-6 hours

---

### REM-103: Implement Account Lockout Mechanism

**Risk:** R-011  
**Control:** CC6.2 (enhancement)  
**Description:** After N failed login attempts, lock account for X minutes.

**Implementation:**
- Track failed login attempts per user/IP
- Lock account after threshold (e.g., 5 failed attempts)
- Unlock after cooldown period (e.g., 15 minutes)
- Store lockout state in database

**Estimated Effort:** 4-6 hours

---

### REM-104: Implement User Data Export Functionality

**Risk:** R-013  
**Control:** Data Management (GDPR/CCPA compliance)  
**Description:** Users should be able to export their data (right to data portability).

**Implementation:**
- Create `/api/user/export` endpoint
- Export user profile, parlays, analytics data
- Format: JSON or CSV
- Secure delivery (email or download link)

**Estimated Effort:** 6-8 hours

---

## P2 - Improvement/Maturity

### REM-201: Configure Long-Term Backup Retention

**Risk:** R-014  
**Control:** CC7.5.4 (enhancement)  
**Description:** Configure long-term backup retention (7 years for audit requirements).

**Implementation:**
- Configure Render backup retention (if available)
- Or implement manual backup export to long-term storage
- Document backup retention schedule

**Estimated Effort:** 2-4 hours

---

### REM-202: Implement Automated Security Alerting

**Risk:** R-015  
**Control:** CC7.3 (enhancement)  
**Description:** Automated alerts for security events (failed logins, unauthorized access, etc.).

**Implementation:**
- Integrate with monitoring service (e.g., Sentry, Datadog)
- Configure alerts for security events
- Email/Slack notifications for critical events

**Estimated Effort:** 4-6 hours

---

### REM-203: Implement Automated Data Retention

**Risk:** R-012  
**Control:** CC6.6.3 (enhancement)  
**Description:** Automated deletion of data after retention period.

**Implementation:**
- Scheduled job for data cleanup
- Delete expired user data
- Delete expired logs
- Document deletion process

**Estimated Effort:** 6-8 hours

---

## Remediation Summary

**P0 Items:** 8 items (estimated 30-40 hours)  
**P1 Items:** 4 items (estimated 22-32 hours)  
**P2 Items:** 3 items (estimated 12-18 hours)

**Total Estimated Effort:** 64-90 hours

---

## Remediation Timeline

**Before Audit (P0):**
- Complete all P0 items
- Estimated time: 4-6 weeks (part-time)

**Post-Audit (P1):**
- Implement P1 items for security maturity
- Estimated time: 3-4 weeks (part-time)

**Ongoing (P2):**
- Implement P2 items as resources allow
- Estimated time: 2-3 weeks (part-time)

---

**Last Updated:** 2025-01-XX  
**Next Review:** As remediation items are completed
