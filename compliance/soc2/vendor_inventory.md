# Vendor Inventory

**Product:** Parlay Gorilla  
**Last Updated:** 2025-01-XX  
**Review Frequency:** Annually

---

## Purpose

This document inventories all third-party vendors and service providers used by Parlay Gorilla, including security assessments and risk ratings.

---

## Vendor Classification

**Critical:** Vendors that handle sensitive data or are essential to core business functions  
**Standard:** Vendors that provide non-critical services  
**Low-Risk:** Vendors that do not handle sensitive data

---

## Vendor Inventory

| Vendor ID | Vendor Name | Service Provided | Classification | Data Handled | Certifications | Risk Rating | Assessment Date | Next Review | Contact |
|-----------|-------------|------------------|----------------|-------------|----------------|-------------|------------------|-------------|---------|
| **V-001** | Render | Infrastructure hosting, PostgreSQL database, Redis | Critical | Application data, user data, payment records | SOC 2 Type II | Low | [To be filled] | [To be filled] | support@render.com |
| **V-002** | Stripe | Payment processing, subscriptions, one-time payments | Critical | Payment data (PCI handled by Stripe, not stored locally) | PCI DSS Level 1, SOC 2 | Low | [To be filled] | [To be filled] | support@stripe.com |
| **V-003** | OpenAI | AI parlay generation, natural language processing | Critical | User prompts, parlay data (may be processed by OpenAI) | SOC 2 | Medium | [To be filled] | [To be filled] | support@openai.com |
| **V-004** | GitHub | Source code repository, version control | Critical | Source code, configuration files | SOC 2 Type II | Low | [To be filled] | [To be filled] | support@github.com |
| **V-005** | The Odds API | Sports odds data, game information | Standard | None (read-only API) | N/A | Low | [To be filled] | [To be filled] | support@the-odds-api.com |
| **V-006** | SportsRadar | Game data, schedules, statistics | Standard | None (read-only API) | N/A | Low | [To be filled] | [To be filled] | support@sportradar.com |
| **V-007** | Resend | Transactional email service | Standard | Email addresses, email content | SOC 2 | Low | [To be filled] | [To be filled] | support@resend.com |
| **V-008** | LemonSqueezy | Payment processing (legacy/fallback) | Standard | Payment data (PCI handled by LemonSqueezy) | PCI DSS | Low | [To be filled] | [To be filled] | support@lemonsqueezy.com |
| **V-009** | Coinbase Commerce | Cryptocurrency payments (deprecated) | Standard | Payment data | N/A | Medium | [To be filled] | [To be filled] | support@coinbase.com |

---

## Vendor Details

### V-001: Render

**Service:** Infrastructure hosting, PostgreSQL database, Redis key-value store

**Data Handled:**
- Application data (user accounts, parlays, analyses)
- User PII (email addresses, usernames)
- Payment records (subscription IDs, transaction metadata)
- System logs

**Access:**
- Render dashboard (team members)
- Database access via Render private network
- API access for deployments

**Security:**
- SOC 2 Type II certified
- Data encrypted at rest and in transit
- Regular security audits
- Incident notification procedures

**Risk Assessment:** Low
- Established provider with strong security practices
- SOC 2 Type II certification
- No known security incidents

**Contract Terms:**
- Terms of Service: https://render.com/terms
- Privacy Policy: https://render.com/privacy
- Data Processing Agreement: [If applicable]

**Incident Notification:** Within 24-48 hours of security incidents

---

### V-002: Stripe

**Service:** Payment processing, subscription management, one-time payments

**Data Handled:**
- Payment card data (PCI handled by Stripe, not stored locally)
- Customer payment information
- Transaction records
- Subscription metadata

**Access:**
- Stripe API (backend application)
- Stripe Dashboard (account owner)

**Security:**
- PCI DSS Level 1 certified
- SOC 2 certified
- Card data never touches our servers
- Webhook signature verification

**Risk Assessment:** Low
- Industry-leading payment processor
- PCI DSS Level 1 compliance
- No known security incidents

**Contract Terms:**
- Terms of Service: https://stripe.com/legal
- Privacy Policy: https://stripe.com/privacy
- Data Processing Agreement: [If applicable]

**Incident Notification:** Within 24-48 hours of security incidents

---

### V-003: OpenAI

**Service:** AI parlay generation, natural language processing

**Data Handled:**
- User prompts (parlay generation requests)
- Parlay data (may be processed by OpenAI)
- Game analysis requests

**Access:**
- OpenAI API (backend application)

**Security:**
- SOC 2 certified
- Data processing policies
- API key authentication

**Risk Assessment:** Medium
- User data may be processed by OpenAI
- Data processing agreement recommended
- No known security incidents

**Contract Terms:**
- Terms of Service: https://openai.com/policies/terms
- Privacy Policy: https://openai.com/policies/privacy
- Data Processing Agreement: [To be reviewed]

**Incident Notification:** Within 24-48 hours of security incidents

---

### V-004: GitHub

**Service:** Source code repository, version control

**Data Handled:**
- Source code
- Configuration files
- Documentation
- Commit history

**Access:**
- GitHub repository (collaborators)
- GitHub API (if used)

**Security:**
- SOC 2 Type II certified
- Repository access controls
- Two-factor authentication support

**Risk Assessment:** Low
- Established provider with strong security practices
- SOC 2 Type II certification
- No known security incidents

**Contract Terms:**
- Terms of Service: https://docs.github.com/en/site-policy/github-terms
- Privacy Policy: https://docs.github.com/en/site-policy/privacy-policies
- Data Processing Agreement: [If applicable]

**Incident Notification:** Within 24-48 hours of security incidents

---

### V-005: The Odds API

**Service:** Sports odds data, game information

**Data Handled:**
- None (read-only API, no user data)

**Access:**
- The Odds API (backend application, API key authentication)

**Security:**
- API key authentication
- HTTPS required

**Risk Assessment:** Low
- Read-only API, no sensitive data
- No known security incidents

**Contract Terms:**
- Terms of Service: [To be reviewed]
- Privacy Policy: [To be reviewed]

**Incident Notification:** [To be determined]

---

### V-006: SportsRadar

**Service:** Game data, schedules, statistics

**Data Handled:**
- None (read-only API, no user data)

**Access:**
- SportsRadar API (backend application, API key authentication)

**Security:**
- API key authentication
- HTTPS required

**Risk Assessment:** Low
- Read-only API, no sensitive data
- No known security incidents

**Contract Terms:**
- Terms of Service: [To be reviewed]
- Privacy Policy: [To be reviewed]

**Incident Notification:** [To be determined]

---

### V-007: Resend

**Service:** Transactional email service

**Data Handled:**
- Email addresses
- Email content (verification emails, password reset emails)

**Access:**
- Resend API (backend application, API key authentication)

**Security:**
- SOC 2 certified
- API key authentication

**Risk Assessment:** Low
- Established email service provider
- SOC 2 certification
- No known security incidents

**Contract Terms:**
- Terms of Service: https://resend.com/legal/terms
- Privacy Policy: https://resend.com/legal/privacy

**Incident Notification:** [To be determined]

---

### V-008: LemonSqueezy

**Service:** Payment processing (legacy/fallback)

**Data Handled:**
- Payment data (PCI handled by LemonSqueezy, not stored locally)

**Access:**
- LemonSqueezy API (backend application)
- LemonSqueezy Dashboard (if applicable)

**Security:**
- PCI DSS compliant
- Webhook signature verification

**Risk Assessment:** Low
- PCI DSS compliance
- No known security incidents

**Contract Terms:**
- Terms of Service: [To be reviewed]
- Privacy Policy: [To be reviewed]

**Incident Notification:** [To be determined]

---

### V-009: Coinbase Commerce

**Service:** Cryptocurrency payments (deprecated)

**Data Handled:**
- Payment data

**Access:**
- Coinbase Commerce API (backend application)

**Security:**
- API key authentication
- Webhook signature verification

**Risk Assessment:** Medium
- Deprecated service (not actively used)
- No known security incidents

**Contract Terms:**
- Terms of Service: [To be reviewed]
- Privacy Policy: [To be reviewed]

**Incident Notification:** [To be determined]

**Status:** Deprecated - kept for reference only

---

## Vendor Risk Summary

### Critical Vendors (4)
- Render (Infrastructure)
- Stripe (Payments)
- OpenAI (AI Services)
- GitHub (Source Control)

### Standard Vendors (4)
- The Odds API (Sports Data)
- SportsRadar (Game Data)
- Resend (Email)
- LemonSqueezy (Payments - legacy)

### Low-Risk Vendors (1)
- Coinbase Commerce (Deprecated)

---

## Vendor Assessment Process

### Initial Assessment
1. Review vendor security documentation
2. Review vendor terms of service and privacy policy
3. Assess data handling procedures
4. Document assessment findings
5. Approve or reject vendor

### Ongoing Assessment
- **Critical Vendors:** Annually
- **Standard Vendors:** Every 2 years
- **Low-Risk Vendors:** As needed

### Assessment Criteria
- Security practices and certifications
- Data handling procedures
- Incident response procedures
- Business continuity plans
- Compliance certifications (SOC 2, PCI DSS, ISO 27001, etc.)

---

## Vendor Incident Management

### Incident Notification Requirements
- Vendors must notify of security incidents affecting our data
- Notification within 24-48 hours of discovery
- Detailed incident report within 7 days

### Incident Response Process
1. Receive vendor incident notification
2. Assess impact on our systems/data
3. Determine response actions
4. Notify affected users if data breach
5. Document incident
6. Review vendor relationship

---

## Vendor Termination

### Termination Process
1. Notify vendor of termination
2. Export data (if applicable)
3. Revoke API keys and access
4. Verify data deletion (if applicable)
5. Update vendor inventory
6. Document termination

---

**Last Updated:** 2025-01-XX  
**Next Review:** Annually
