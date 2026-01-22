# Risk Register

**Product:** Parlay Gorilla  
**Last Updated:** 2025-01-XX  
**Review Frequency:** Quarterly

---

## Risk Assessment Methodology

**Risk Score = Likelihood × Impact**

**Likelihood:**
- **High (3):** Likely to occur
- **Medium (2):** Possible
- **Low (1):** Unlikely

**Impact:**
- **High (3):** Critical business impact
- **Medium (2):** Significant impact
- **Low (1):** Minor impact

**Risk Rating:**
- **Critical (9):** Immediate action required
- **High (6):** Action required within 30 days
- **Medium (4):** Action required within 90 days
- **Low (2-3):** Monitor and address as resources allow

---

## Risk Register

| Risk ID | Risk Description | Category | Likelihood | Impact | Risk Score | Current Controls | Residual Risk | Remediation | Owner | Status |
|---------|------------------|----------|------------|--------|------------|------------------|---------------|-------------|-------|--------|
| **R-001** | JWT tokens stored in localStorage (XSS risk) | Authentication | Medium | High | 6 | HttpOnly cookies also set (hybrid), XSS prevention in React | Medium | Implement refresh tokens, migrate to HttpOnly-only storage | Dev Team | ⚠️ Remediation Required |
| **R-002** | No JWT refresh token mechanism | Authentication | Medium | Medium | 4 | 24-hour token expiration, rate limiting | Medium | Implement refresh token flow | Dev Team | ⚠️ Remediation Required |
| **R-003** | No MFA for admin accounts | Access Control | Medium | High | 6 | Strong passwords, admin role checks | High | Implement TOTP MFA for admin accounts | Dev Team | ⚠️ Remediation Required |
| **R-004** | No MFA for infrastructure access (Render, GitHub) | Access Control | Low | High | 3 | Strong passwords, access reviews | Medium | Enable MFA on Render and GitHub accounts | Dev Team | ⚠️ Remediation Required |
| **R-005** | No password policy enforcement | Authentication | Medium | Medium | 4 | Password hashing (PBKDF2-SHA256) | Medium | Implement password complexity requirements | Dev Team | ⚠️ Remediation Required |
| **R-006** | Limited security event logging | Monitoring | Medium | Medium | 4 | System logs, payment event logs | Medium | Implement comprehensive security event logging | Dev Team | ⚠️ Remediation Required |
| **R-007** | No admin action logging | Monitoring | Medium | High | 6 | Admin role checks, access controls | High | Implement admin action audit log | Dev Team | ⚠️ Remediation Required |
| **R-008** | No secrets rotation process | Secrets Management | Low | High | 3 | Secrets in Render env vars, auto-generated JWT_SECRET | Medium | Document and implement secrets rotation schedule | Dev Team | ⚠️ Process Required |
| **R-009** | No backup verification process | Backup/Recovery | Low | High | 3 | Daily backups (Render), Git version control | Medium | Implement quarterly backup restoration testing | Dev Team | ⚠️ Process Required |
| **R-010** | No automated log retention/cleanup | Logging | Medium | Low | 2 | System logs table, manual retention | Low | Implement automated log cleanup (90 days operational, 1 year security) | Dev Team | ⚠️ Process Required |
| **R-011** | No account lockout mechanism | Authentication | Low | Medium | 2 | Rate limiting (10 attempts/minute) | Low | Implement account lockout after N failed attempts | Dev Team | ⚠️ Enhancement |
| **R-012** | No data retention automation | Data Management | Medium | Low | 2 | Data retention policy documented | Low | Implement automated data deletion after retention period | Dev Team | ⚠️ Enhancement |
| **R-013** | No user data export functionality | Data Management | Low | Low | 1 | Data accessible via API | Low | Implement user data export endpoint (GDPR/CCPA compliance) | Dev Team | ⚠️ Enhancement |
| **R-014** | No long-term backup retention | Backup/Recovery | Low | Medium | 2 | 7-day backups (Render default) | Medium | Configure long-term backup retention (7 years for audit) | Dev Team | ⚠️ Enhancement |
| **R-015** | No automated security alerting | Monitoring | Medium | Medium | 4 | Manual log monitoring | Medium | Implement automated alerts for security events | Dev Team | ⚠️ Enhancement |

---

## Risk Categories

### Authentication & Authorization
- R-001: JWT token storage (XSS risk)
- R-002: No refresh tokens
- R-003: No admin MFA
- R-005: No password policy
- R-011: No account lockout

### Access Control
- R-003: No admin MFA
- R-004: No infrastructure MFA

### Monitoring & Logging
- R-006: Limited security event logging
- R-007: No admin action logging
- R-010: No automated log retention
- R-015: No automated security alerting

### Secrets Management
- R-008: No secrets rotation process

### Backup & Recovery
- R-009: No backup verification
- R-014: No long-term backup retention

### Data Management
- R-012: No data retention automation
- R-013: No user data export

---

## Risk Mitigation Summary

### Critical Risks (Score 9)
- None identified

### High Risks (Score 6)
- **R-001:** JWT token storage (XSS risk) - Remediation required
- **R-003:** No admin MFA - Remediation required
- **R-007:** No admin action logging - Remediation required

### Medium Risks (Score 4)
- **R-002:** No refresh tokens - Remediation required
- **R-005:** No password policy - Remediation required
- **R-006:** Limited security event logging - Remediation required
- **R-015:** No automated security alerting - Enhancement

### Low Risks (Score 2-3)
- **R-004:** No infrastructure MFA - Remediation required
- **R-008:** No secrets rotation - Process required
- **R-009:** No backup verification - Process required
- **R-010:** No automated log retention - Process required
- **R-011:** No account lockout - Enhancement
- **R-012:** No data retention automation - Enhancement
- **R-013:** No user data export - Enhancement
- **R-014:** No long-term backup retention - Enhancement

---

## Risk Treatment

### Accept
- **R-013:** No user data export (low risk, can be addressed post-audit)

### Mitigate
- All other risks require mitigation via remediation, process implementation, or enhancement

### Transfer
- Payment card data risk transferred to Stripe (PCI DSS compliance)

### Avoid
- None (all risks are acceptable with proper controls)

---

## Next Steps

1. Address P0 remediation items (R-001, R-003, R-007)
2. Implement P1 remediation items (R-002, R-005, R-006)
3. Document and implement P2 processes (R-008, R-009, R-010)
4. Plan enhancements (R-011, R-012, R-013, R-014, R-015)

---

**Last Updated:** 2025-01-XX  
**Next Review:** Quarterly
