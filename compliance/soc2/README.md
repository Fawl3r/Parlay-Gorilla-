# SOC 2 Type I Readiness Documentation

**Product:** Parlay Gorilla  
**Hosting:** Render (Frontend + Backend)  
**Database:** Render PostgreSQL  
**Auth:** Custom JWT-based  
**Payments:** Stripe (PCI handled by Stripe)  
**Status:** Pre-Audit Readiness Assessment

---

## Purpose

This directory contains documentation and controls for SOC 2 Type I readiness under the **Security Trust Service Criteria**. This is **readiness preparation**, not a claim of compliance.

---

## Directory Structure

```
compliance/
├── soc2/
│   ├── README.md (this file)
│   ├── controls_matrix.md
│   ├── risk_register.md
│   ├── asset_inventory.md
│   ├── vendor_inventory.md
│   └── evidence_index.md
└── policies/
    ├── information_security_policy.md
    ├── access_control_policy.md
    ├── authentication_policy.md
    ├── incident_response_plan.md
    ├── change_management_policy.md
    ├── vulnerability_management_policy.md
    ├── backup_and_recovery_policy.md
    ├── vendor_management_policy.md
    ├── data_retention_policy.md
    ├── secure_sdlc_policy.md
    └── acceptable_use_policy.md
```

---

## How to Use This Documentation

1. **For Auditors:** Start with `controls_matrix.md` to understand control coverage
2. **For Remediation:** Review `risk_register.md` and remediation backlog in `controls_matrix.md`
3. **For Evidence Collection:** Use `evidence_index.md` to gather required artifacts
4. **For Policy Reference:** All policies are in `compliance/policies/`

---

## Key Controls Summary

### Strong Areas ✅
- Webhook signature verification (Stripe, LemonSqueezy, Coinbase)
- Password hashing (PBKDF2-SHA256 with legacy bcrypt support)
- Rate limiting on auth endpoints
- Role-based access control (admin/mod/user)
- Secrets managed via Render environment variables
- Database parameterized queries (SQLAlchemy)

### Areas Requiring Remediation ⚠️
- JWT refresh token strategy (currently 24h expiration, no refresh)
- MFA enforcement (not implemented)
- Secrets rotation process (not documented)
- Security event logging (limited coverage)
- Backup verification process (not documented)
- Change management via GitHub PRs (process not formalized)

---

## Next Steps

1. Review `controls_matrix.md` for complete control mapping
2. Address P0 remediation items before audit
3. Collect evidence per `evidence_index.md`
4. Update policies as controls are implemented

---

**Last Updated:** 2025-01-XX  
**Maintained By:** Development Team  
**Review Frequency:** Quarterly
