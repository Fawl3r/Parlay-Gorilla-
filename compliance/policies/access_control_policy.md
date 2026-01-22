# Access Control Policy

**Policy ID:** ACCESS-001  
**Version:** 1.0  
**Effective Date:** 2025-01-XX  
**Review Frequency:** Quarterly  
**Owner:** Development Team

---

## 1. Purpose

This policy defines access control requirements for Parlay Gorilla systems, ensuring that only authorized personnel have access to appropriate resources based on their roles and responsibilities.

---

## 2. Scope

This policy applies to:
- **Application Access:** User accounts, admin accounts, API access
- **Infrastructure Access:** Render dashboard, GitHub repositories, database access
- **Third-Party Services:** Stripe dashboard, OpenAI account, The Odds API account

---

## 3. Access Control Principles

### 3.1 Principle of Least Privilege
Users are granted the minimum level of access necessary to perform their job functions.

### 3.2 Role-Based Access Control (RBAC)
Access is granted based on predefined roles:
- **User:** Standard application users (default role)
- **Moderator:** Can moderate content, view analytics (limited admin functions)
- **Admin:** Full system access, user management, payment reconciliation

### 3.3 Separation of Duties
Administrative functions separated from regular user functions. No single user should have all administrative privileges without oversight.

---

## 4. Application-Level Access Control

### 4.1 User Roles

**User Role (`user`):**
- Access to: Own account, parlay generation, custom builder, analytics dashboard
- Cannot access: Admin endpoints, other users' data, system configuration

**Moderator Role (`mod`):**
- Access to: All user functions, content moderation, analytics viewing
- Cannot access: User account management, payment reconciliation, system configuration

**Admin Role (`admin`):**
- Access to: All system functions, user management, payment reconciliation, system logs, feature flags
- Admin endpoints: `/api/admin/*` (see `backend/app/api/routes/admin/`)

### 4.2 Role Enforcement

**Backend Implementation:**
- Role checks via `require_admin()` and `require_mod_or_admin()` dependencies
- Location: `backend/app/api/routes/admin/auth.py`
- All admin endpoints require `role == "admin"` in User model

**Frontend Implementation:**
- Admin routes protected by `AdminLayout` component
- Location: `frontend/app/admin/layout.tsx`
- Redirects non-admin users to home page

### 4.3 Access Control Code References

```python
# Admin dependency
async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != UserRole.admin.value:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
```

**File:** `backend/app/api/routes/admin/auth.py`

---

## 5. Infrastructure Access Control

### 5.1 Render Dashboard Access
- **Access Method:** Email/password authentication
- **MFA Requirement:** MFA should be enabled (see Remediation Backlog)
- **Access Levels:**
  - **Owner:** Full access to all services, environment variables, database
  - **Member:** Read-only access (if applicable)

### 5.2 GitHub Repository Access
- **Access Method:** GitHub authentication (SSH keys or personal access tokens)
- **MFA Requirement:** MFA should be enabled (see Remediation Backlog)
- **Access Levels:**
  - **Admin:** Full repository access, can manage collaborators
  - **Write:** Can push code, create pull requests
  - **Read:** Can view code, cannot modify

### 5.3 Database Access
- **Production Database:** Accessible only via Render private network
- **Direct Access:** Not permitted for production database
- **Migration Access:** Via Alembic migrations, executed during Render deployments
- **Backup Access:** Via Render dashboard (read-only)

### 5.4 API Key Management
- **Stripe API Keys:** Stored in Render environment variables, accessed via Stripe dashboard
- **OpenAI API Keys:** Stored in Render environment variables
- **The Odds API Keys:** Stored in Render environment variables
- **Webhook Secrets:** Stored in Render environment variables (STRIPE_WEBHOOK_SECRET, etc.)

---

## 6. Access Provisioning

### 6.1 New User Registration
- Users self-register via `/api/auth/register`
- Default role: `user`
- Email verification required (if enabled)
- Profile completion required before full access

### 6.2 Admin Account Creation
- Admin accounts created manually via database or admin script
- Location: `backend/scripts/grant_lifetime_membership.py` (example)
- **Process:**
  1. Create user account via standard registration or direct DB insert
  2. Update `users.role` to `"admin"` via database query or admin script
  3. Verify admin access via `/api/admin/auth/login`

### 6.3 Infrastructure Access Provisioning
- Render dashboard: Invited via email by account owner
- GitHub: Added as collaborator by repository admin
- Third-party services: Access granted by account owner

---

## 7. Access Review and Revocation

### 7.1 Access Reviews
- **Frequency:** Quarterly
- **Scope:** All admin accounts, Render dashboard access, GitHub access
- **Process:**
  1. List all users with `role == "admin"`
  2. Verify each admin account is still needed
  3. Review Render dashboard access
  4. Review GitHub repository access
  5. Document review in access review log

### 7.2 Access Revocation
- **Immediate Revocation:** When employee termination, security incident, or policy violation
- **Process:**
  1. Remove admin role from user account (set `role = "user"`)
  2. Revoke Render dashboard access (if applicable)
  3. Revoke GitHub access (if applicable)
  4. Revoke third-party service access (if applicable)
  5. Document revocation in access revocation log

### 7.3 Inactive Account Management
- **Inactive Threshold:** 90 days without login
- **Action:** Review for deactivation (not automatically deactivated)
- **Location:** `users.last_login` field tracked in database

---

## 8. Access Logging

### 8.1 Application Access Logs
- **Login Events:** Logged to database (user.last_login updated)
- **Admin Actions:** Should be logged (see Remediation Backlog)
- **Failed Login Attempts:** Rate limiting prevents brute force, but not explicitly logged

### 8.2 Infrastructure Access Logs
- **Render Dashboard:** Access logs available in Render dashboard
- **GitHub:** Access logs available in GitHub repository settings
- **Database:** Connection logs available in Render PostgreSQL logs

---

## 9. Emergency Access

### 9.1 Break-Glass Procedures
In case of emergency requiring immediate access:
1. Document emergency reason
2. Grant temporary access
3. Revoke access immediately after emergency resolved
4. Review access in next quarterly review

### 9.2 Service Account Access
- **Render Service Accounts:** Not used (single account model)
- **GitHub Service Accounts:** Not used (personal access tokens if needed)

---

## 10. Compliance

This policy supports SOC 2 Type I readiness under **Security Trust Service Criteria CC6.1** (Logical and physical access controls).

---

## 11. Policy Review

This policy is reviewed quarterly or when:
- New roles are added
- Access control mechanisms change
- Security incidents occur

---

**Approved By:** [To be filled]  
**Last Review Date:** [To be filled]  
**Next Review Date:** [To be filled]
