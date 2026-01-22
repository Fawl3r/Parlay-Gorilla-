# Information Security Policy

**Policy ID:** INFOSEC-001  
**Version:** 1.0  
**Effective Date:** 2025-01-XX  
**Review Frequency:** Annually  
**Owner:** Development Team

---

## 1. Purpose

This policy establishes the framework for protecting Parlay Gorilla's information assets, including customer data, application code, and infrastructure components. This policy applies to all systems, services, and personnel involved in the development, deployment, and operation of Parlay Gorilla.

---

## 2. Scope

This policy applies to:
- **Application:** Parlay Gorilla web application (Next.js frontend, FastAPI backend)
- **Infrastructure:** Render-hosted services (frontend, backend, PostgreSQL database, Redis)
- **Source Control:** GitHub repositories
- **Third-Party Services:** Stripe (payments), OpenAI (AI generation), The Odds API (sports data)
- **Personnel:** All developers, administrators, and contractors with system access

---

## 3. Information Classification

### 3.1 Confidential Data
- **Customer PII:** Email addresses, usernames, passwords (hashed)
- **Payment Data:** Stripe customer IDs, subscription IDs (card data handled by Stripe, not stored locally)
- **Authentication Secrets:** JWT signing keys, API keys, webhook secrets
- **Database Credentials:** PostgreSQL connection strings

### 3.2 Internal Data
- **Application Logs:** System logs, error logs, access logs
- **Analytics Data:** User behavior, feature usage (non-PII)
- **Configuration:** Non-sensitive environment variables

### 3.3 Public Data
- **Marketing Content:** Public website content, blog posts
- **Documentation:** Public API documentation (non-sensitive endpoints)

---

## 4. Security Controls

### 4.1 Access Control
- **Principle of Least Privilege:** Users granted minimum access necessary
- **Role-Based Access:** Admin, Moderator, and User roles enforced at application level
- **Authentication Required:** All administrative and user-facing endpoints require authentication
- **Session Management:** JWT tokens expire after 24 hours (see Authentication Policy)

### 4.2 Data Protection
- **Encryption in Transit:** All external communications use HTTPS/TLS
- **Encryption at Rest:** Render PostgreSQL databases encrypted at rest (Render-managed)
- **Password Hashing:** Passwords hashed using PBKDF2-SHA256 (legacy bcrypt supported)
- **Secrets Management:** All secrets stored in Render environment variables, never in code

### 4.3 Network Security
- **HTTPS Enforcement:** All public endpoints require HTTPS
- **Database Access:** PostgreSQL accessible only via Render private network or VPN
- **API Rate Limiting:** Authentication endpoints rate-limited to prevent brute force attacks

### 4.4 Application Security
- **Input Validation:** All user inputs validated and sanitized
- **SQL Injection Prevention:** Parameterized queries via SQLAlchemy ORM
- **XSS Prevention:** Frontend uses React with automatic escaping
- **CSRF Protection:** State-changing operations require authentication tokens
- **Webhook Security:** All webhook endpoints verify HMAC signatures

### 4.5 Logging and Monitoring
- **Security Events:** Authentication failures, admin actions, webhook events logged
- **System Logs:** Application errors, API failures logged to `system_logs` table
- **Access Logs:** User login/logout events tracked
- **Payment Events:** All payment webhook events logged to `payment_events` table

---

## 5. Incident Response

See **Incident Response Plan** (`incident_response_plan.md`) for detailed procedures.

**Summary:**
- Security incidents must be reported within 24 hours
- Critical incidents (data breach, unauthorized access) require immediate response
- All incidents documented in incident log

---

## 6. Change Management

See **Change Management Policy** (`change_management_policy.md`) for detailed procedures.

**Summary:**
- All code changes via GitHub pull requests
- Production deployments via Render automatic deploys from GitHub
- Database migrations via Alembic, tested in staging before production

---

## 7. Vulnerability Management

See **Vulnerability Management Policy** (`vulnerability_management_policy.md`) for detailed procedures.

**Summary:**
- Dependencies scanned for known vulnerabilities
- Security patches applied within 30 days for critical vulnerabilities
- Regular dependency updates scheduled quarterly

---

## 8. Backup and Recovery

See **Backup and Recovery Policy** (`backup_and_recovery_policy.md`) for detailed procedures.

**Summary:**
- Render PostgreSQL automatic daily backups
- Backup restoration tested quarterly
- Database migrations reversible via Alembic versioning

---

## 9. Vendor Management

See **Vendor Management Policy** (`vendor_management_policy.md`) for detailed procedures.

**Summary:**
- Third-party vendors assessed for security practices
- Vendor access limited to minimum necessary
- Vendor security incidents reviewed quarterly

---

## 10. Compliance

This policy supports SOC 2 Type I readiness under the **Security Trust Service Criteria**.

**Key Trust Criteria Addressed:**
- CC6.1: Logical and physical access controls
- CC6.2: System access authentication
- CC6.6: Data transmission and disposal
- CC6.7: System boundaries and data classification
- CC7.2: System monitoring and logging

---

## 11. Enforcement

Violations of this policy may result in:
- Revocation of system access
- Disciplinary action
- Legal action if applicable

---

## 12. Policy Review

This policy is reviewed annually or when significant changes occur to:
- Application architecture
- Infrastructure hosting
- Regulatory requirements
- Security threats

---

## 13. Contact

**Security Questions:** Contact development team  
**Incident Reporting:** Follow procedures in `incident_response_plan.md`

---

**Approved By:** [To be filled]  
**Last Review Date:** [To be filled]  
**Next Review Date:** [To be filled]
