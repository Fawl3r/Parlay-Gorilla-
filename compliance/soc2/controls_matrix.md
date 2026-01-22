# SOC 2 Controls Matrix

**Product:** Parlay Gorilla  
**Trust Criteria:** Security  
**Type:** Type I Readiness  
**Last Updated:** 2025-01-XX

---

## Overview

This matrix maps SOC 2 Security Trust Service Criteria to implemented controls, evidence requirements, and remediation items.

---

## Controls Matrix

| Control ID | Trust Criteria | Control Description | System / Scope | Control Owner | Evidence Required | How Evidence Is Generated | Status |
|------------|----------------|---------------------|----------------|---------------|-------------------|---------------------------|--------|
| **CC6.1 - Logical Access Controls** |
| CC6.1.1 | CC6.1 | Role-based access control (RBAC) implemented | Application (Backend/Frontend) | Dev Team | Code review, User model schema, Admin endpoint tests | GitHub PR reviews, `backend/app/models/user.py`, `backend/app/api/routes/admin/auth.py` | ✅ Implemented |
| CC6.1.2 | CC6.1 | Admin access requires admin role verification | Application (Backend) | Dev Team | Code review, Admin endpoint implementation | `backend/app/api/routes/admin/auth.py` → `require_admin()` | ✅ Implemented |
| CC6.1.3 | CC6.1 | User access limited to own data | Application (Backend) | Dev Team | Code review, API endpoint tests | `backend/app/core/dependencies.py` → `get_current_user()` | ✅ Implemented |
| CC6.1.4 | CC6.1 | Infrastructure access (Render, GitHub) requires authentication | Infrastructure | Dev Team | Render dashboard access logs, GitHub access logs | Render dashboard → Access logs, GitHub → Settings → Security → Access logs | ✅ Implemented |
| CC6.1.5 | CC6.1 | MFA enabled for infrastructure access | Infrastructure | Dev Team | MFA configuration screenshots | Render dashboard → Account → Security, GitHub → Settings → Security | ⚠️ Remediation Required |
| CC6.1.6 | CC6.1 | Access reviews conducted quarterly | All Systems | Dev Team | Access review log, Quarterly review documentation | Manual review, document in access review log | ⚠️ Process Required |
| **CC6.2 - Authentication** |
| CC6.2.1 | CC6.2 | User authentication via email/password | Application (Backend) | Dev Team | Code review, Login endpoint tests | `backend/app/api/routes/auth.py` → `login()` | ✅ Implemented |
| CC6.2.2 | CC6.2 | Passwords hashed using PBKDF2-SHA256 | Application (Backend) | Dev Team | Code review, Password hasher implementation | `backend/app/services/auth/password_hasher.py` | ✅ Implemented |
| CC6.2.3 | CC6.2 | JWT tokens used for session management | Application (Backend/Frontend) | Dev Team | Code review, Token generation/validation | `backend/app/services/auth_service.py` → `create_access_token()`, `decode_access_token()` | ✅ Implemented |
| CC6.2.4 | CC6.2 | JWT tokens expire after 24 hours | Application (Backend) | Dev Team | Code review, Configuration | `backend/app/services/auth_service.py` → `ACCESS_TOKEN_EXPIRE_HOURS = 24` | ✅ Implemented |
| CC6.2.5 | CC6.2 | JWT refresh token mechanism | Application (Backend) | Dev Team | Code review, Refresh endpoint | N/A - Not implemented | ⚠️ Remediation Required |
| CC6.2.6 | CC6.2 | Rate limiting on authentication endpoints | Application (Backend) | Dev Team | Code review, Rate limit decorators | `backend/app/api/routes/auth.py` → `@rate_limit("10/minute")` | ✅ Implemented |
| CC6.2.7 | CC6.2 | MFA for admin accounts | Application (Backend) | Dev Team | MFA implementation, Admin login flow | N/A - Not implemented | ⚠️ Remediation Required |
| CC6.2.8 | CC6.2 | Password policy enforcement | Application (Backend) | Dev Team | Code review, Password validation | N/A - Not implemented | ⚠️ Remediation Required |
| **CC6.3 - Authorization** |
| CC6.3.1 | CC6.3 | API endpoints protected by authentication | Application (Backend) | Dev Team | Code review, Dependency injection | `backend/app/core/dependencies.py` → `get_current_user()` | ✅ Implemented |
| CC6.3.2 | CC6.3 | Admin endpoints require admin role | Application (Backend) | Dev Team | Code review, Admin dependencies | `backend/app/api/routes/admin/auth.py` → `require_admin()` | ✅ Implemented |
| CC6.3.3 | CC6.3 | Webhook endpoints verify signatures | Application (Backend) | Dev Team | Code review, Webhook handlers | `backend/app/api/routes/webhooks/stripe_webhook_routes.py`, `lemonsqueezy_webhook_routes.py` | ✅ Implemented |
| **CC6.6 - Data Transmission and Disposal** |
| CC6.6.1 | CC6.6 | HTTPS enforced for all external communications | Infrastructure | Render | SSL/TLS configuration, Certificate details | Render dashboard → Service → Settings → SSL | ✅ Implemented |
| CC6.6.2 | CC6.6 | Database encrypted at rest | Infrastructure | Render | Database encryption documentation | Render PostgreSQL documentation | ✅ Implemented (Render-managed) |
| CC6.6.3 | CC6.6 | Data retention policy implemented | Application (Backend) | Dev Team | Data retention policy, Retention implementation | `compliance/policies/data_retention_policy.md` | ⚠️ Process Required |
| CC6.6.4 | CC6.6 | Secure data disposal procedures | Application (Backend) | Dev Team | Data deletion procedures, Deletion logs | Data retention policy, Deletion scripts | ⚠️ Process Required |
| **CC6.7 - System Boundaries** |
| CC6.7.1 | CC6.7 | System boundaries defined and documented | All Systems | Dev Team | Architecture documentation, System diagrams | `compliance/soc2/asset_inventory.md` | ✅ Documented |
| CC6.7.2 | CC6.7 | Data classification policy implemented | All Systems | Dev Team | Data classification policy | `compliance/policies/information_security_policy.md` → Section 3 | ✅ Documented |
| CC6.7.3 | CC6.7 | Network segmentation (production vs development) | Infrastructure | Render | Environment separation, Database access controls | Render dashboard → Services, Database access logs | ✅ Implemented |
| **CC7.1 - System Monitoring** |
| CC7.1.1 | CC7.1 | System logs captured and stored | Application (Backend) | Dev Team | System logs table, Log entries | `backend/app/models/system_log.py`, `system_logs` table queries | ✅ Implemented |
| CC7.1.2 | CC7.1 | Payment events logged | Application (Backend) | Dev Team | Payment events table, Event entries | `backend/app/models/payment_event.py`, `payment_events` table queries | ✅ Implemented |
| CC7.1.3 | CC7.1 | Security events logged (auth failures, admin actions) | Application (Backend) | Dev Team | Security event log, Event entries | N/A - Limited implementation | ⚠️ Remediation Required |
| CC7.1.4 | CC7.1 | Logs retained for 90 days (operational) or 1 year (security) | Application (Backend) | Dev Team | Log retention configuration, Retention logs | Log cleanup scripts, Retention documentation | ⚠️ Process Required |
| CC7.1.5 | CC7.1 | Infrastructure monitoring (Render dashboard) | Infrastructure | Render | Render service health, Metrics | Render dashboard → Service → Metrics | ✅ Implemented |
| **CC7.2 - System Monitoring and Logging** |
| CC7.2.1 | CC7.2 | Application errors logged | Application (Backend) | Dev Team | System logs, Error entries | `system_logs` table, `level = "error"` | ✅ Implemented |
| CC7.2.2 | CC7.2 | Authentication events logged | Application (Backend) | Dev Team | User login tracking, Last login updates | `users.last_login` field, Login endpoint logs | ⚠️ Partial (needs enhancement) |
| CC7.2.3 | CC7.2 | Admin actions logged | Application (Backend) | Dev Team | Admin action log, Action entries | N/A - Not implemented | ⚠️ Remediation Required |
| **CC7.3 - System Security Event Monitoring** |
| CC7.3.1 | CC7.3 | Failed authentication attempts monitored | Application (Backend) | Dev Team | Rate limiting logs, Failed login tracking | Rate limiting prevents brute force, but not explicitly logged | ⚠️ Remediation Required |
| CC7.3.2 | CC7.3 | Unauthorized access attempts monitored | Application (Backend) | Dev Team | Security event log, Access attempt entries | N/A - Not implemented | ⚠️ Remediation Required |
| CC7.3.3 | CC7.3 | Security incident response procedures | All Systems | Dev Team | Incident response plan, Incident logs | `compliance/policies/incident_response_plan.md` | ✅ Documented |
| **CC7.4 - System Security Event Monitoring** |
| CC7.4.1 | CC7.4 | Vulnerability scanning conducted | Application (Backend/Frontend) | Dev Team | Dependency scan results, Vulnerability reports | GitHub Dependabot alerts, Manual dependency audits | ✅ Implemented |
| CC7.4.2 | CC7.4 | Vulnerabilities remediated per policy | Application (Backend/Frontend) | Dev Team | Vulnerability remediation log, Patch deployment | Dependency updates, Security patch logs | ✅ Process Implemented |
| CC7.4.3 | CC7.4 | Security patches applied within 30 days (critical) | Application (Backend/Frontend) | Dev Team | Patch deployment logs, Vulnerability tracking | Dependency updates, Security patch documentation | ✅ Process Implemented |
| **CC7.5 - System Backup and Recovery** |
| CC7.5.1 | CC7.5 | Database backups performed daily | Infrastructure | Render | Backup configuration, Backup logs | Render dashboard → Database → Backups | ✅ Implemented (Render-managed) |
| CC7.5.2 | CC7.5 | Backup restoration tested quarterly | Infrastructure | Dev Team | Backup test documentation, Test results | Manual backup restoration test, Test documentation | ⚠️ Process Required |
| CC7.5.3 | CC7.5 | Code backups via Git version control | Infrastructure | GitHub | Git repository, Commit history | GitHub repository, Git log | ✅ Implemented |
| CC7.5.4 | CC7.5 | Backup retention policy implemented | Infrastructure | Render/Dev Team | Backup retention configuration, Retention logs | Render backup retention (7 days), Long-term backup policy | ⚠️ Process Required |
| **CC8.1 - Change Management** |
| CC8.1.1 | CC8.1 | Code changes via GitHub pull requests | Infrastructure | Dev Team | GitHub PR history, PR reviews | GitHub repository → Pull requests | ✅ Implemented |
| CC8.1.2 | CC8.1 | Code review required before merge | Infrastructure | Dev Team | PR review logs, Approval records | GitHub PR reviews, Approval status | ✅ Implemented |
| CC8.1.3 | CC8.1 | Database migrations via Alembic | Application (Backend) | Dev Team | Migration files, Migration execution logs | `backend/alembic/versions/`, Render deployment logs | ✅ Implemented |
| CC8.1.4 | CC8.1 | Change management policy documented | All Systems | Dev Team | Change management policy | `compliance/policies/change_management_policy.md` | ✅ Documented |
| CC8.1.5 | CC8.1 | Production deployments via Render automatic deploys | Infrastructure | Render | Deployment logs, Deployment history | Render dashboard → Service → Deployments | ✅ Implemented |
| **CC8.2 - System Development and Maintenance** |
| CC8.2.1 | CC8.2 | Secure SDLC policy documented | Application (Backend/Frontend) | Dev Team | Secure SDLC policy | `compliance/policies/secure_sdlc_policy.md` | ✅ Documented |
| CC8.2.2 | CC8.2 | Input validation on all user inputs | Application (Backend) | Dev Team | Code review, Pydantic models | `backend/app/api/routes/auth.py` → Pydantic request models | ✅ Implemented |
| CC8.2.3 | CC8.2 | SQL injection prevention (parameterized queries) | Application (Backend) | Dev Team | Code review, SQLAlchemy usage | SQLAlchemy ORM (all queries parameterized) | ✅ Implemented |
| CC8.2.4 | CC8.2 | Secrets management (no secrets in code) | Application (Backend) | Dev Team | Code review, Environment variable usage | Render environment variables, `backend/app/core/config.py` | ✅ Implemented |
| **CC8.3 - System Development and Maintenance** |
| CC8.3.1 | CC8.3 | Dependency vulnerability scanning | Application (Backend/Frontend) | Dev Team | Dependency scan results, Vulnerability reports | GitHub Dependabot alerts, `npm audit`, `pip-audit` | ✅ Implemented |
| CC8.3.2 | CC8.3 | Dependencies updated regularly | Application (Backend/Frontend) | Dev Team | Dependency update logs, Update history | Dependency updates, Security patch logs | ✅ Process Implemented |

---

## Legend

- ✅ **Implemented:** Control is implemented and operational
- ⚠️ **Remediation Required:** Control needs implementation or enhancement
- ⚠️ **Process Required:** Control needs process documentation or formalization

---

## Remediation Backlog

See detailed remediation items in `controls_matrix.md` remediation section (to be added) and `risk_register.md`.

**Priority Summary:**
- **P0 (Must Fix Before Audit):** 8 items
- **P1 (Should Fix):** 6 items
- **P2 (Improvement/Maturity):** 4 items

---

**Last Updated:** 2025-01-XX  
**Next Review:** Quarterly
