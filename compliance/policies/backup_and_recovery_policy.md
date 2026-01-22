# Backup and Recovery Policy

**Policy ID:** BACKUP-001  
**Version:** 1.0  
**Effective Date:** 2025-01-XX  
**Review Frequency:** Quarterly  
**Owner:** Development Team

---

## 1. Purpose

This policy defines backup and recovery procedures for Parlay Gorilla systems and data, ensuring data availability and recoverability in case of data loss, corruption, or system failures.

---

## 2. Scope

This policy applies to:
- **Database:** Render PostgreSQL database (parlay-gorilla-postgres)
- **Application Code:** GitHub repository
- **Configuration:** Render environment variables, render.yaml
- **Logs:** Application logs, system logs (retention)

---

## 3. Backup Requirements

### 3.1 Database Backups

**Provider:** Render PostgreSQL automatic backups

**Backup Frequency:**
- **Automatic:** Daily backups (Render-managed)
- **Manual:** On-demand backups via Render dashboard (before major changes)

**Backup Retention:**
- **Daily Backups:** 7 days (Render default)
- **Long-term:** [To be configured - see Remediation Backlog]

**Backup Location:**
- Render-managed storage (encrypted at rest)
- Accessible via Render dashboard

**Backup Verification:**
- **Frequency:** Quarterly (see Remediation Backlog)
- **Process:**
  1. Restore backup to test database
  2. Verify data integrity
  3. Verify schema consistency
  4. Document verification results

### 3.2 Code Backups

**Provider:** GitHub repository

**Backup Method:**
- Git version control (automatic)
- All code changes tracked in Git history
- Remote repository on GitHub (redundant storage)

**Backup Retention:**
- Permanent (Git history)
- All commits, branches, tags preserved

**Backup Verification:**
- GitHub repository accessible
- Code can be cloned and restored
- No additional verification needed (Git is self-verifying)

### 3.3 Configuration Backups

**Environment Variables:**
- **Storage:** Render dashboard (encrypted)
- **Backup Method:** Export to secure document (quarterly)
- **Location:** [Secure document storage - see Remediation Backlog]

**render.yaml:**
- **Storage:** GitHub repository
- **Backup Method:** Git version control (automatic)

**Backup Verification:**
- Configuration documented in repository
- Environment variables exported quarterly

---

## 4. Recovery Procedures

### 4.1 Database Recovery

**Scenario 1: Data Corruption**

**Process:**
1. Identify corruption (error logs, data inconsistencies)
2. Determine point-in-time for recovery
3. Restore from Render backup:
   - Render Dashboard → Database → Backups
   - Select backup point
   - Restore to new database or replace existing
4. Verify data integrity
5. Update application connection string if needed
6. Monitor for issues

**Recovery Time Objective (RTO):** 4 hours
**Recovery Point Objective (RPO):** 24 hours (daily backups)

**Scenario 2: Accidental Data Deletion**

**Process:**
1. Identify deleted data
2. Determine deletion time
3. Restore from backup before deletion
4. Extract missing data
5. Merge with current database (if needed)
6. Verify data integrity

**Scenario 3: Complete Database Loss**

**Process:**
1. Create new database in Render
2. Restore from most recent backup
3. Run database migrations (Alembic) to ensure schema is current
4. Update application connection string
5. Verify application functionality
6. Monitor for issues

**Recovery Time:** 2-4 hours

### 4.2 Code Recovery

**Scenario: Bad Deployment**

**Process:**
1. Identify issue (error logs, user reports)
2. Revert commit in GitHub:
   ```bash
   git revert <commit-hash>
   git push origin main
   ```
3. Render automatically redeploys previous version
4. Verify functionality restored
5. Monitor for issues

**Recovery Time:** 15-30 minutes

**Scenario: Repository Loss**

**Process:**
1. Clone from GitHub (if accessible)
2. If GitHub inaccessible, restore from local clone
3. Verify code integrity
4. Push to new repository if needed

### 4.3 Configuration Recovery

**Scenario: Environment Variable Loss**

**Process:**
1. Restore from backup document
2. Re-enter variables in Render dashboard
3. Restart services
4. Verify configuration loaded

**Recovery Time:** 30 minutes

---

## 5. Backup Testing

### 5.1 Database Backup Testing

**Frequency:** Quarterly

**Process:**
1. Create test database in Render
2. Restore production backup to test database
3. Verify:
   - Data integrity (sample queries)
   - Schema consistency (Alembic version check)
   - Application connectivity
4. Document test results
5. Clean up test database

**Documentation:**
- Test date
- Backup version tested
- Test results
- Issues found (if any)
- Remediation (if needed)

### 5.2 Code Backup Testing

**Frequency:** Not required (Git is self-verifying)

**Verification:**
- GitHub repository accessible
- Code can be cloned
- Build succeeds

### 5.3 Configuration Backup Testing

**Frequency:** Quarterly

**Process:**
1. Verify backup document exists
2. Verify all environment variables documented
3. Test restoration process (dry run)
4. Document test results

---

## 6. Backup Storage

### 6.1 Storage Locations

**Database Backups:**
- Render-managed storage (encrypted)
- Accessible via Render dashboard

**Code Backups:**
- GitHub repository (primary)
- Local developer clones (redundant)

**Configuration Backups:**
- Secure document storage (encrypted)
- [Location to be determined - see Remediation Backlog]

### 6.2 Storage Security

**Encryption:**
- Database backups: Encrypted at rest (Render-managed)
- Configuration backups: Encrypted document storage

**Access Control:**
- Database backups: Render dashboard access only
- Configuration backups: Restricted access (team members only)

**Retention:**
- Database backups: 7 days (Render default)
- Code backups: Permanent (Git)
- Configuration backups: 7 years

---

## 7. Disaster Recovery

### 7.1 Disaster Scenarios

**Complete Infrastructure Loss:**
- Render service failure
- Database loss
- Code repository loss

**Recovery Process:**
1. Restore database from backup
2. Restore code from GitHub
3. Recreate Render services (render.yaml)
4. Restore environment variables
5. Deploy application
6. Verify functionality

**Recovery Time Objective (RTO):** 24 hours
**Recovery Point Objective (RPO):** 24 hours (daily backups)

### 7.2 Business Continuity

**Critical Functions:**
- User authentication
- Payment processing (Stripe)
- Parlay generation

**Priority:**
1. Restore authentication system
2. Restore payment processing
3. Restore core application features

---

## 8. Backup Monitoring

### 8.1 Backup Status Monitoring

**Database Backups:**
- Monitor Render dashboard for backup status
- Verify backups completing successfully
- Alert on backup failures

**Code Backups:**
- GitHub repository accessible
- No additional monitoring needed

**Configuration Backups:**
- Verify backup document updated quarterly
- Alert on missed backups

### 8.2 Backup Alerts

**Current Status:** Manual monitoring (see Remediation Backlog)

**Recommended:**
- Automated backup success/failure alerts
- Backup verification reminders
- Retention policy alerts

---

## 9. Compliance

This policy supports SOC 2 Type I readiness under **Security Trust Service Criteria CC7.5** (System backup and recovery).

---

## 10. Policy Review

This policy is reviewed quarterly or when:
- Backup procedures change
- Recovery time requirements change
- Significant incidents occur

---

**Approved By:** [To be filled]  
**Last Review Date:** [To be filled]  
**Next Review Date:** [To be filled]
