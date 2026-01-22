# Evidence Index

**Product:** Parlay Gorilla  
**Trust Criteria:** Security  
**Type:** Type I Readiness  
**Last Updated:** 2025-01-XX

---

## Purpose

This document identifies all evidence artifacts required for SOC 2 Type I audit, including location, collection method, and frequency.

---

## Evidence Collection Overview

**Evidence Types:**
- **Code Artifacts:** Source code, configuration files, database migrations
- **Configuration:** Environment variables, infrastructure configuration
- **Logs:** Application logs, access logs, security event logs
- **Documentation:** Policies, procedures, architecture diagrams
- **Screenshots:** Infrastructure configuration, access controls
- **Reports:** Vulnerability scans, dependency audits, access reviews

---

## Evidence by Trust Criteria

### CC6.1 - Logical Access Controls

| Evidence ID | Evidence Description | Location | Collection Method | Frequency | Retention |
|-------------|----------------------|----------|-------------------|-----------|-----------|
| **E-CC6.1.1** | Role-based access control implementation | `backend/app/models/user.py` | Code review, Git history | One-time | Permanent (Git) |
| **E-CC6.1.2** | Admin access control code | `backend/app/api/routes/admin/auth.py` | Code review, Git history | One-time | Permanent (Git) |
| **E-CC6.1.3** | User model schema (roles) | `backend/app/models/user.py` → `role` field | Database schema export | One-time | Permanent (Git) |
| **E-CC6.1.4** | Render dashboard access logs | Render Dashboard → Account → Access Logs | Screenshot, export | Quarterly | 1 year |
| **E-CC6.1.5** | GitHub repository access logs | GitHub → Settings → Security → Access Logs | Screenshot, export | Quarterly | 1 year |
| **E-CC6.1.6** | MFA configuration (Render) | Render Dashboard → Account → Security → MFA | Screenshot | One-time | 1 year |
| **E-CC6.1.7** | MFA configuration (GitHub) | GitHub → Settings → Security → Two-factor authentication | Screenshot | One-time | 1 year |
| **E-CC6.1.8** | Access review log | Access review document | Manual documentation | Quarterly | 7 years |

---

### CC6.2 - Authentication

| Evidence ID | Evidence Description | Location | Collection Method | Frequency | Retention |
|-------------|----------------------|----------|-------------------|-----------|-----------|
| **E-CC6.2.1** | Authentication implementation | `backend/app/api/routes/auth.py` → `login()` | Code review, Git history | One-time | Permanent (Git) |
| **E-CC6.2.2** | Password hashing implementation | `backend/app/services/auth/password_hasher.py` | Code review, Git history | One-time | Permanent (Git) |
| **E-CC6.2.3** | JWT token generation | `backend/app/services/auth_service.py` → `create_access_token()` | Code review, Git history | One-time | Permanent (Git) |
| **E-CC6.2.4** | JWT token validation | `backend/app/core/dependencies.py` → `get_current_user()` | Code review, Git history | One-time | Permanent (Git) |
| **E-CC6.2.5** | JWT expiration configuration | `backend/app/services/auth_service.py` → `ACCESS_TOKEN_EXPIRE_HOURS = 24` | Code review | One-time | Permanent (Git) |
| **E-CC6.2.6** | Rate limiting implementation | `backend/app/api/routes/auth.py` → `@rate_limit()` | Code review, Git history | One-time | Permanent (Git) |
| **E-CC6.2.7** | Password reset implementation | `backend/app/api/routes/auth.py` → `forgot_password()`, `reset_password()` | Code review, Git history | One-time | Permanent (Git) |
| **E-CC6.2.8** | Authentication test results | `backend/tests/test_auth_flows.py` | Test execution, test results | Ongoing | 1 year |

---

### CC6.3 - Authorization

| Evidence ID | Evidence Description | Location | Collection Method | Frequency | Retention |
|-------------|----------------------|----------|-------------------|-----------|-----------|
| **E-CC6.3.1** | Protected endpoint implementation | `backend/app/core/dependencies.py` → `get_current_user()` | Code review, Git history | One-time | Permanent (Git) |
| **E-CC6.3.2** | Admin endpoint protection | `backend/app/api/routes/admin/auth.py` → `require_admin()` | Code review, Git history | One-time | Permanent (Git) |
| **E-CC6.3.3** | Webhook signature verification (Stripe) | `backend/app/api/routes/webhooks/stripe_webhook_routes.py` | Code review, Git history | One-time | Permanent (Git) |
| **E-CC6.3.4** | Webhook signature verification (LemonSqueezy) | `backend/app/api/routes/webhooks/lemonsqueezy_webhook_routes.py` | Code review, Git history | One-time | Permanent (Git) |
| **E-CC6.3.5** | Webhook signature verification (Coinbase) | `backend/app/api/routes/webhooks/coinbase_webhook_routes.py` | Code review, Git history | One-time | Permanent (Git) |

---

### CC6.6 - Data Transmission and Disposal

| Evidence ID | Evidence Description | Location | Collection Method | Frequency | Retention |
|-------------|----------------------|----------|-------------------|-----------|-----------|
| **E-CC6.6.1** | HTTPS/TLS configuration | Render Dashboard → Service → Settings → SSL | Screenshot | One-time | 1 year |
| **E-CC6.6.2** | SSL certificate details | Render Dashboard → Service → Settings → SSL | Screenshot, export | One-time | 1 year |
| **E-CC6.6.3** | Database encryption documentation | Render documentation | Documentation reference | One-time | 1 year |
| **E-CC6.6.4** | Data retention policy | `compliance/policies/data_retention_policy.md` | Policy document | One-time | Permanent |
| **E-CC6.6.5** | Data deletion procedures | Data retention policy, deletion scripts | Documentation, code review | One-time | Permanent |

---

### CC6.7 - System Boundaries

| Evidence ID | Evidence Description | Location | Collection Method | Frequency | Retention |
|-------------|----------------------|----------|-------------------|-----------|-----------|
| **E-CC6.7.1** | Asset inventory | `compliance/soc2/asset_inventory.md` | Documentation | Quarterly | Permanent |
| **E-CC6.7.2** | System architecture diagram | Architecture documentation | Diagram, documentation | One-time | Permanent |
| **E-CC6.7.3** | Data classification policy | `compliance/policies/information_security_policy.md` → Section 3 | Policy document | One-time | Permanent |
| **E-CC6.7.4** | Environment separation (production vs development) | Render Dashboard → Services | Screenshot, documentation | One-time | 1 year |

---

### CC7.1 - System Monitoring

| Evidence ID | Evidence Description | Location | Collection Method | Frequency | Retention |
|-------------|----------------------|----------|-------------------|-----------|-----------|
| **E-CC7.1.1** | System logs table schema | `backend/app/models/system_log.py` | Code review, database schema | One-time | Permanent (Git) |
| **E-CC7.1.2** | System logs sample | `system_logs` table query | Database query, export | Quarterly | 1 year |
| **E-CC7.1.3** | Payment events table schema | `backend/app/models/payment_event.py` | Code review, database schema | One-time | Permanent (Git) |
| **E-CC7.1.4** | Payment events sample | `payment_events` table query | Database query, export | Quarterly | 1 year |
| **E-CC7.1.5** | Security event log (when implemented) | Security event log table | Database query, export | Quarterly | 1 year |
| **E-CC7.1.6** | Log retention configuration | Log cleanup scripts, configuration | Code review, documentation | One-time | Permanent (Git) |
| **E-CC7.1.7** | Render service health metrics | Render Dashboard → Service → Metrics | Screenshot, export | Quarterly | 1 year |

---

### CC7.2 - System Monitoring and Logging

| Evidence ID | Evidence Description | Location | Collection Method | Frequency | Retention |
|-------------|----------------------|----------|-------------------|-----------|-----------|
| **E-CC7.2.1** | Error logging implementation | `backend/app/models/system_log.py` | Code review, Git history | One-time | Permanent (Git) |
| **E-CC7.2.2** | Error logs sample | `system_logs` table (level=error) | Database query, export | Quarterly | 1 year |
| **E-CC7.2.3** | Authentication event logging | `users.last_login` field, login endpoint | Database query, code review | Quarterly | 1 year |
| **E-CC7.2.4** | Admin action log (when implemented) | Admin action log table | Database query, export | Quarterly | 1 year |

---

### CC7.3 - System Security Event Monitoring

| Evidence ID | Evidence Description | Location | Collection Method | Frequency | Retention |
|-------------|----------------------|----------|-------------------|-----------|-----------|
| **E-CC7.3.1** | Failed authentication monitoring | Rate limiting logs, security event log | Database query, export | Quarterly | 1 year |
| **E-CC7.3.2** | Unauthorized access monitoring | Security event log | Database query, export | Quarterly | 1 year |
| **E-CC7.3.3** | Incident response plan | `compliance/policies/incident_response_plan.md` | Policy document | One-time | Permanent |
| **E-CC7.3.4** | Incident log | Incident log document | Manual documentation | As incidents occur | 7 years |

---

### CC7.4 - System Security Event Monitoring

| Evidence ID | Evidence Description | Location | Collection Method | Frequency | Retention |
|-------------|----------------------|----------|-------------------|-----------|-----------|
| **E-CC7.4.1** | Dependency vulnerability scan results | GitHub Dependabot alerts | Screenshot, export | Quarterly | 1 year |
| **E-CC7.4.2** | Manual dependency audit results | Dependency audit document | Manual documentation | Quarterly | 1 year |
| **E-CC7.4.3** | Vulnerability remediation log | Vulnerability tracking document | Manual documentation | As vulnerabilities remediated | 7 years |
| **E-CC7.4.4** | Security patch deployment logs | Git commit history, deployment logs | Git log, Render deployment logs | As patches deployed | 1 year |

---

### CC7.5 - System Backup and Recovery

| Evidence ID | Evidence Description | Location | Collection Method | Frequency | Retention |
|-------------|----------------------|----------|-------------------|-----------|-----------|
| **E-CC7.5.1** | Database backup configuration | Render Dashboard → Database → Backups | Screenshot | One-time | 1 year |
| **E-CC7.5.2** | Database backup logs | Render Dashboard → Database → Backups | Screenshot, export | Quarterly | 1 year |
| **E-CC7.5.3** | Backup restoration test results | Backup test documentation | Manual documentation | Quarterly | 7 years |
| **E-CC7.5.4** | Code backup (Git repository) | GitHub repository | Git log, repository access | One-time | Permanent (Git) |
| **E-CC7.5.5** | Backup retention policy | `compliance/policies/backup_and_recovery_policy.md` | Policy document | One-time | Permanent |

---

### CC8.1 - Change Management

| Evidence ID | Evidence Description | Location | Collection Method | Frequency | Retention |
|-------------|----------------------|----------|-------------------|-----------|-----------|
| **E-CC8.1.1** | GitHub pull request history | GitHub → Pull requests | Screenshot, export | Quarterly | Permanent (Git) |
| **E-CC8.1.2** | Code review records | GitHub PR reviews | Screenshot, export | Quarterly | Permanent (Git) |
| **E-CC8.1.3** | Database migration files | `backend/alembic/versions/` | Code review, Git history | One-time | Permanent (Git) |
| **E-CC8.1.4** | Migration execution logs | Render deployment logs | Screenshot, export | Quarterly | 1 year |
| **E-CC8.1.5** | Change management policy | `compliance/policies/change_management_policy.md` | Policy document | One-time | Permanent |
| **E-CC8.1.6** | Production deployment logs | Render Dashboard → Service → Deployments | Screenshot, export | Quarterly | 1 year |

---

### CC8.2 - System Development and Maintenance

| Evidence ID | Evidence Description | Location | Collection Method | Frequency | Retention |
|-------------|----------------------|----------|-------------------|-----------|-----------|
| **E-CC8.2.1** | Secure SDLC policy | `compliance/policies/secure_sdlc_policy.md` | Policy document | One-time | Permanent |
| **E-CC8.2.2** | Input validation implementation | `backend/app/api/routes/auth.py` → Pydantic models | Code review, Git history | One-time | Permanent (Git) |
| **E-CC8.2.3** | SQL injection prevention | SQLAlchemy ORM usage | Code review, Git history | One-time | Permanent (Git) |
| **E-CC8.2.4** | Secrets management (no secrets in code) | `backend/app/core/config.py`, Render env vars | Code review, configuration review | One-time | Permanent |

---

### CC8.3 - System Development and Maintenance

| Evidence ID | Evidence Description | Location | Collection Method | Frequency | Retention |
|-------------|----------------------|----------|-------------------|-----------|-----------|
| **E-CC8.3.1** | Dependency vulnerability scan results | GitHub Dependabot alerts | Screenshot, export | Quarterly | 1 year |
| **E-CC8.3.2** | Dependency update logs | Git commit history | Git log | Quarterly | Permanent (Git) |
| **E-CC8.3.3** | Security patch deployment | Git commit history, deployment logs | Git log, Render logs | As patches deployed | 1 year |

---

## Evidence Collection Schedule

### One-Time Collection
- Code artifacts (source code, configuration files)
- Policy documents
- Architecture diagrams
- Infrastructure configuration screenshots

### Quarterly Collection
- Access logs (Render, GitHub)
- System logs samples
- Payment events samples
- Vulnerability scan results
- Deployment logs
- Backup verification test results

### Ongoing Collection
- Security incidents (as they occur)
- Vulnerability remediations (as they occur)
- Access reviews (quarterly)
- Backup tests (quarterly)

---

## Evidence Storage

**Location:**
- **Code Artifacts:** GitHub repository (permanent)
- **Documentation:** `compliance/` directory (permanent)
- **Logs:** Database tables, Render logs (retention per policy)
- **Screenshots/Exports:** Secure document storage (1-7 years per retention policy)

**Access Control:**
- Evidence accessible to development team
- Sensitive evidence (logs with PII) restricted access
- Evidence reviewed quarterly

---

## Evidence Collection Procedures

### Code Artifacts
1. Review Git history for relevant commits
2. Export code files or provide Git links
3. Document code review findings

### Configuration
1. Screenshot infrastructure configuration
2. Export environment variable lists (masked)
3. Document configuration settings

### Logs
1. Query database for log samples
2. Export logs (CSV or JSON format)
3. Mask PII if present
4. Document log retention

### Documentation
1. Review policy documents
2. Verify documentation is up to date
3. Export policy documents

---

**Last Updated:** 2025-01-XX  
**Next Review:** Quarterly
