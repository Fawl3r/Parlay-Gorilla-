# Vendor Management Policy

**Policy ID:** VENDOR-001  
**Version:** 1.0  
**Effective Date:** 2025-01-XX  
**Review Frequency:** Annually  
**Owner:** Development Team

---

## 1. Purpose

This policy defines procedures for managing third-party vendors and service providers, ensuring that vendor relationships are properly assessed, monitored, and managed to protect Parlay Gorilla's data and systems.

---

## 2. Scope

This policy applies to:
- **Infrastructure Vendors:** Render (hosting, database)
- **Payment Processors:** Stripe (card payments)
- **API Providers:** OpenAI (AI generation), The Odds API (sports data), SportsRadar (game data)
- **Development Tools:** GitHub (source control)
- **Email Services:** Resend (transactional emails)

---

## 3. Vendor Classification

### 3.1 Critical Vendors

**Definition:** Vendors that handle sensitive data or are essential to core business functions

**Vendors:**
- **Render:** Hosting, database, infrastructure
- **Stripe:** Payment processing, customer payment data
- **OpenAI:** AI generation (may process user data)
- **GitHub:** Source code repository

**Requirements:**
- Annual security assessment
- SOC 2 or equivalent certification (preferred)
- Data processing agreement (if applicable)
- Incident notification procedures

### 3.2 Standard Vendors

**Definition:** Vendors that provide non-critical services

**Vendors:**
- **The Odds API:** Sports odds data
- **SportsRadar:** Game data, schedules
- **Resend:** Transactional emails
- **OpenWeather:** Weather data

**Requirements:**
- Initial security assessment
- Security incident notification
- Periodic review (every 2 years)

### 3.3 Low-Risk Vendors

**Definition:** Vendors that do not handle sensitive data

**Vendors:**
- **Pexels:** Stock images
- **Unsplash:** Stock images

**Requirements:**
- Basic security review
- Review as needed

---

## 4. Vendor Assessment

### 4.1 Initial Assessment

**Assessment Criteria:**
- Security practices and certifications
- Data handling procedures
- Incident response procedures
- Business continuity plans
- Compliance certifications (SOC 2, ISO 27001, etc.)

**Assessment Process:**
1. Review vendor security documentation
2. Review vendor terms of service and privacy policy
3. Assess data handling procedures
4. Document assessment findings
5. Approve or reject vendor

**Documentation:**
- Vendor name and service
- Assessment date
- Assessment findings
- Approval status
- Risk rating

### 4.2 Ongoing Assessment

**Frequency:**
- Critical vendors: Annually
- Standard vendors: Every 2 years
- Low-risk vendors: As needed

**Assessment Process:**
1. Review vendor security updates
2. Review vendor incident reports
3. Assess continued suitability
4. Update vendor record

---

## 5. Vendor Inventory

### 5.1 Current Vendors

**Infrastructure:**
- **Render:** Hosting, PostgreSQL database, Redis
  - **Data Handled:** Application data, user data, payment data
  - **Certifications:** SOC 2 Type II (Render)
  - **Assessment Date:** [To be filled]
  - **Next Review:** [To be filled]

**Payment Processing:**
- **Stripe:** Card payments, subscriptions
  - **Data Handled:** Payment data (PCI handled by Stripe)
  - **Certifications:** PCI DSS Level 1 (Stripe)
  - **Assessment Date:** [To be filled]
  - **Next Review:** [To be filled]

**AI Services:**
- **OpenAI:** AI parlay generation
  - **Data Handled:** User prompts, parlay data (may be processed)
  - **Certifications:** SOC 2 (OpenAI)
  - **Assessment Date:** [To be filled]
  - **Next Review:** [To be filled]

**Source Control:**
- **GitHub:** Code repository
  - **Data Handled:** Source code, configuration
  - **Certifications:** SOC 2 Type II (GitHub)
  - **Assessment Date:** [To be filled]
  - **Next Review:** [To be filled]

**API Providers:**
- **The Odds API:** Sports odds data
  - **Data Handled:** None (read-only API)
  - **Assessment Date:** [To be filled]
  - **Next Review:** [To be filled]

- **SportsRadar:** Game data, schedules
  - **Data Handled:** None (read-only API)
  - **Assessment Date:** [To be filled]
  - **Next Review:** [To be filled]

**Email Services:**
- **Resend:** Transactional emails
  - **Data Handled:** Email addresses, email content
  - **Assessment Date:** [To be filled]
  - **Next Review:** [To be filled]

### 5.2 Vendor Record Format

**Required Fields:**
- Vendor name
- Service provided
- Data classification (Confidential/Internal/Public)
- Data handled
- Certifications
- Assessment date
- Next review date
- Risk rating (Critical/Standard/Low)
- Contact information

**Storage:**
- Location: `compliance/soc2/vendor_inventory.md`
- Update frequency: As vendors are added/removed

---

## 6. Vendor Access Management

### 6.1 Access Principles

**Principle of Least Privilege:**
- Vendors granted minimum access necessary
- Access reviewed quarterly
- Access revoked when no longer needed

### 6.2 Access Types

**API Access:**
- API keys stored in Render environment variables
- Keys rotated periodically (see Remediation Backlog)
- Keys revoked if compromised

**Dashboard Access:**
- Render dashboard: Team members only
- Stripe dashboard: Account owner only
- GitHub: Repository collaborators only

---

## 7. Vendor Incident Management

### 7.1 Vendor Incident Notification

**Requirements:**
- Vendors must notify of security incidents affecting our data
- Notification within 24-48 hours of discovery
- Detailed incident report within 7 days

### 7.2 Incident Response

**Process:**
1. Receive vendor incident notification
2. Assess impact on our systems/data
3. Determine response actions
4. Notify affected users if data breach
5. Document incident
6. Review vendor relationship

---

## 8. Vendor Contract Management

### 8.1 Contract Requirements

**Required Clauses:**
- Data protection and security requirements
- Incident notification procedures
- Data breach notification (within 24-48 hours)
- Right to audit (if applicable)
- Data return/deletion upon termination

### 8.2 Contract Review

**Frequency:** Annually or when contract renews

**Review Process:**
1. Review contract terms
2. Verify security requirements met
3. Update vendor record
4. Renew or terminate as appropriate

---

## 9. Vendor Termination

### 9.1 Termination Process

**Process:**
1. Notify vendor of termination
2. Export data (if applicable)
3. Revoke API keys and access
4. Verify data deletion (if applicable)
5. Update vendor inventory
6. Document termination

### 9.2 Data Migration

**Requirements:**
- Export all data before termination
- Verify data completeness
- Secure data storage
- Update systems to remove vendor dependencies

---

## 10. Compliance

This policy supports SOC 2 Type I readiness under **Security Trust Service Criteria CC6.3** (System access authorization) and **CC7.1** (System security monitoring).

---

## 11. Policy Review

This policy is reviewed annually or when:
- New vendors are added
- Vendor incidents occur
- Regulatory requirements change

---

**Approved By:** [To be filled]  
**Last Review Date:** [To be filled]  
**Next Review Date:** [To be filled]
