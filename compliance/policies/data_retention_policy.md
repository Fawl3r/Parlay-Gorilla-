# Data Retention Policy

**Policy ID:** DATA-001  
**Version:** 1.0  
**Effective Date:** 2025-01-XX  
**Review Frequency:** Annually  
**Owner:** Development Team

---

## 1. Purpose

This policy defines data retention periods and disposal procedures for Parlay Gorilla data, ensuring compliance with legal requirements and business needs while minimizing data exposure risk.

---

## 2. Scope

This policy applies to:
- **User Data:** User accounts, profiles, authentication data
- **Application Data:** Parlays, analyses, analytics data
- **Payment Data:** Subscription records, payment events, transaction logs
- **System Data:** Application logs, system logs, error logs
- **Backup Data:** Database backups, configuration backups

---

## 3. Data Classification

### 3.1 Personal Identifiable Information (PII)

**Definition:** Data that can identify an individual

**Examples:**
- Email addresses
- Usernames
- IP addresses (if stored)
- Account numbers (non-PII by design - 20-char hex)

**Retention:** Active account + 7 years after account deletion

### 3.2 Payment Data

**Definition:** Data related to payments and subscriptions

**Examples:**
- Subscription records
- Payment event logs
- Stripe customer IDs
- Transaction metadata

**Retention:** 7 years (tax/audit requirements)

**Note:** Card data handled by Stripe, not stored locally

### 3.3 Application Data

**Definition:** User-generated content and application data

**Examples:**
- Generated parlays
- Custom parlay analyses
- Saved parlays
- Analytics data

**Retention:** Active account + 1 year after account deletion

### 3.4 System Data

**Definition:** System logs, error logs, operational data

**Examples:**
- Application logs (`system_logs` table)
- Error logs
- Access logs
- Performance metrics

**Retention:** 90 days (operational), 1 year (security events)

### 3.5 Backup Data

**Definition:** Database backups, configuration backups

**Retention:** 7 days (daily backups), 7 years (long-term if configured)

---

## 4. Retention Periods

### 4.1 User Account Data

**Active Accounts:**
- **Retention:** Indefinite (while account is active)
- **Deletion:** Upon user request or account inactivity (90+ days)

**Deleted Accounts:**
- **Retention:** 7 years after deletion
- **Reason:** Legal/audit requirements
- **Process:** Soft delete (mark as deleted, retain data)

**Implementation:**
- Location: `users` table
- Soft delete: `users.is_active = False` or `users.deleted_at` timestamp
- Hard delete: After 7 years

### 4.2 Payment Data

**Subscription Records:**
- **Retention:** 7 years after subscription ends
- **Reason:** Tax/audit requirements
- **Location:** `subscriptions` table, `payment_events` table

**Payment Events:**
- **Retention:** 7 years
- **Reason:** Audit trail, dispute resolution
- **Location:** `payment_events` table

### 4.3 Application Data

**Generated Parlays:**
- **Retention:** Active account + 1 year after account deletion
- **Location:** `parlays` table

**Custom Parlays:**
- **Retention:** Active account + 1 year after account deletion
- **Location:** `custom_parlays` table

**Analytics Data:**
- **Retention:** Active account + 1 year after account deletion
- **Location:** `app_events` table

### 4.4 System Logs

**Application Logs:**
- **Retention:** 90 days
- **Location:** `system_logs` table
- **Process:** Automated cleanup (see Remediation Backlog)

**Security Events:**
- **Retention:** 1 year
- **Location:** Security event log (to be implemented)
- **Process:** Manual review before deletion

**Error Logs:**
- **Retention:** 90 days
- **Location:** `system_logs` table (level = "error")
- **Process:** Automated cleanup

### 4.5 Backup Data

**Database Backups:**
- **Retention:** 7 days (Render default)
- **Location:** Render-managed storage
- **Long-term:** [To be configured - see Remediation Backlog]

**Configuration Backups:**
- **Retention:** 7 years
- **Location:** Secure document storage

---

## 5. Data Deletion Procedures

### 5.1 User-Requested Deletion

**Process:**
1. User requests account deletion (via UI or support)
2. Verify user identity
3. Soft delete account (`users.is_active = False`, set `deleted_at`)
4. Anonymize PII (email, username) after 30 days
5. Retain non-PII data for 7 years (audit requirements)
6. Hard delete after 7 years

**Anonymization:**
- Email: `deleted_user_{id}@deleted.local`
- Username: `deleted_user_{id}`
- Password hash: Set to null (cannot authenticate)

### 5.2 Automated Deletion

**Inactive Accounts:**
- **Threshold:** 90 days without login
- **Action:** Review for deletion (not automatic)
- **Process:** Manual review, then user notification before deletion

**Expired Data:**
- **System Logs:** Automated cleanup after 90 days
- **Backups:** Automated deletion after retention period
- **Process:** Scheduled jobs (to be implemented - see Remediation Backlog)

### 5.3 Hard Deletion

**Process:**
1. Verify retention period expired
2. Delete records from database
3. Verify deletion successful
4. Document deletion
5. Update retention log

**Verification:**
- Query database to confirm records deleted
- Verify backups also deleted (if applicable)
- Document deletion date and records deleted

---

## 6. Data Export

### 6.1 User Data Export

**Right to Data Portability:**
- Users can request export of their data
- Export includes: Profile data, parlays, analytics data
- Format: JSON or CSV
- Delivery: Email or secure download link

**Process:**
1. User requests data export
2. Verify user identity
3. Generate export file
4. Deliver to user
5. Log export request

**Implementation:**
- Endpoint: `/api/user/export` (to be implemented - see Remediation Backlog)
- Format: JSON
- Includes: User profile, parlays, custom parlays, analytics

### 6.2 Export Format

**User Data Export:**
```json
{
  "user": {
    "email": "user@example.com",
    "username": "username",
    "created_at": "2024-01-01T00:00:00Z",
    "subscription_status": "active"
  },
  "parlays": [...],
  "custom_parlays": [...],
  "analytics": [...]
}
```

---

## 7. Legal and Regulatory Requirements

### 7.1 Applicable Regulations

**GDPR (if applicable):**
- Right to erasure (deletion)
- Right to data portability
- Data minimization
- Retention limits

**CCPA (if applicable):**
- Right to deletion
- Right to know (data collection)
- Right to opt-out

**Tax/Audit Requirements:**
- Payment data: 7 years
- Financial records: 7 years

### 7.2 Compliance Measures

**Data Minimization:**
- Collect only necessary data
- Delete data when no longer needed
- Anonymize data when possible

**User Rights:**
- Right to access data
- Right to deletion
- Right to data portability
- Right to correction

---

## 8. Data Disposal

### 8.1 Secure Disposal

**Database Records:**
- Delete using SQL DELETE statements
- Verify deletion
- Document disposal

**Backup Data:**
- Delete backups after retention period
- Verify deletion from backup storage
- Document disposal

**Configuration Data:**
- Delete from secure storage
- Verify deletion
- Document disposal

### 8.2 Disposal Verification

**Requirements:**
- Verify data deleted from primary storage
- Verify data deleted from backups
- Verify data deleted from logs
- Document verification

---

## 9. Compliance

This policy supports SOC 2 Type I readiness under **Security Trust Service Criteria CC6.6** (Data transmission and disposal).

---

## 10. Policy Review

This policy is reviewed annually or when:
- Legal requirements change
- Business needs change
- Data types change

---

**Approved By:** [To be filled]  
**Last Review Date:** [To be filled]  
**Next Review Date:** [To be filled]
