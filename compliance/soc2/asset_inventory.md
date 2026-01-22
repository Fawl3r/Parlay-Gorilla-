# Asset Inventory

**Product:** Parlay Gorilla  
**Last Updated:** 2025-01-XX  
**Review Frequency:** Quarterly

---

## Purpose

This document inventories all assets (systems, data, infrastructure) within the scope of SOC 2 Type I readiness assessment.

---

## Asset Classification

**Critical:** Assets essential to business operations, loss would cause significant impact  
**High:** Important assets, loss would cause moderate impact  
**Medium:** Standard assets, loss would cause minor impact  
**Low:** Non-critical assets, loss would cause minimal impact

---

## Infrastructure Assets

### Production Infrastructure

| Asset ID | Asset Name | Type | Provider | Classification | Data Stored | Access Method | Owner |
|----------|------------|------|----------|----------------|-------------|---------------|-------|
| **INF-001** | parlay-gorilla-frontend | Web Service | Render | Critical | None (static assets) | HTTPS (www.parlaygorilla.com) | Dev Team |
| **INF-002** | parlay-gorilla-backend | Web Service | Render | Critical | Application logic, API | HTTPS (api.parlaygorilla.com) | Dev Team |
| **INF-003** | parlay-gorilla-postgres | Database | Render | Critical | User data, application data, payment records | Render private network | Dev Team |
| **INF-004** | parlay-gorilla-redis | Key-Value Store | Render | High | Cache, job queues | Render private network | Dev Team |
| **INF-005** | parlay-gorilla-verification-worker | Worker Service | Render | Medium | Verification queue processing | Render private network | Dev Team |

### Development Infrastructure

| Asset ID | Asset Name | Type | Provider | Classification | Data Stored | Access Method | Owner |
|----------|------------|------|----------|----------------|-------------|---------------|-------|
| **INF-006** | Local PostgreSQL (Docker) | Database | Docker | Medium | Test data | localhost:5432 | Dev Team |
| **INF-007** | Local Redis (Docker) | Key-Value Store | Docker | Low | Test cache | localhost:6379 | Dev Team |

---

## Application Assets

### Backend Application

| Asset ID | Asset Name | Type | Location | Classification | Description |
|----------|------------|------|----------|----------------|-------------|
| **APP-001** | FastAPI Backend | Application Code | `backend/app/` | Critical | Main application logic, API endpoints |
| **APP-002** | Database Models | Application Code | `backend/app/models/` | Critical | Data models, schema definitions |
| **APP-003** | API Routes | Application Code | `backend/app/api/routes/` | Critical | API endpoint implementations |
| **APP-004** | Authentication Service | Application Code | `backend/app/services/auth_service.py` | Critical | JWT token generation, password hashing |
| **APP-005** | Configuration | Application Code | `backend/app/core/config.py` | Critical | Application settings, environment variable loading |
| **APP-006** | Database Migrations | Application Code | `backend/alembic/versions/` | Critical | Database schema versioning |

### Frontend Application

| Asset ID | Asset Name | Type | Location | Classification | Description |
|----------|------------|------|----------|----------------|-------------|
| **APP-007** | Next.js Frontend | Application Code | `frontend/app/` | Critical | User interface, client-side logic |
| **APP-008** | Authentication Context | Application Code | `frontend/lib/auth-context.tsx` | Critical | Client-side authentication state |
| **APP-009** | API Client | Application Code | `frontend/lib/api/` | Critical | Backend API communication |

---

## Data Assets

### User Data

| Asset ID | Asset Name | Type | Location | Classification | Sensitivity | Retention |
|----------|------------|------|----------|----------------|-------------|------------|
| **DATA-001** | User Accounts | Database Table | `users` table | Critical | PII (email, username) | Active + 7 years |
| **DATA-002** | User Passwords | Database Table | `users.password_hash` | Critical | Confidential (hashed) | Active + 7 years |
| **DATA-003** | User Profiles | Database Table | `users` table | High | PII (email, username, display name) | Active + 7 years |
| **DATA-004** | Account Numbers | Database Table | `users.account_number` | Medium | Non-PII (20-char hex) | Active + 7 years |

### Application Data

| Asset ID | Asset Name | Type | Location | Classification | Sensitivity | Retention |
|----------|------------|------|----------|----------------|-------------|------------|
| **DATA-005** | Generated Parlays | Database Table | `parlays` table | High | User-generated content | Active + 1 year |
| **DATA-006** | Custom Parlays | Database Table | `custom_parlays` table | High | User-generated content | Active + 1 year |
| **DATA-007** | Game Analyses | Database Table | `analyses` table | Medium | Public content | Indefinite |
| **DATA-008** | Analytics Events | Database Table | `app_events` table | Medium | User behavior (non-PII) | Active + 1 year |

### Payment Data

| Asset ID | Asset Name | Type | Location | Classification | Sensitivity | Retention |
|----------|------------|------|----------|----------------|-------------|------------|
| **DATA-009** | Subscriptions | Database Table | `subscriptions` table | Critical | Payment records | 7 years |
| **DATA-010** | Payment Events | Database Table | `payment_events` table | Critical | Payment transaction logs | 7 years |
| **DATA-011** | Stripe Customer IDs | Database Table | `users.stripe_customer_id` | High | Payment identifiers | 7 years |
| **DATA-012** | Credit Pack Purchases | Database Table | `credit_pack_purchases` table | High | Payment records | 7 years |

**Note:** Card data handled by Stripe, not stored locally (PCI DSS compliance via Stripe)

### System Data

| Asset ID | Asset Name | Type | Location | Classification | Sensitivity | Retention |
|----------|------------|------|----------|----------------|-------------|------------|
| **DATA-013** | System Logs | Database Table | `system_logs` table | Medium | Operational data | 90 days (operational), 1 year (security) |
| **DATA-014** | Error Logs | Database Table | `system_logs` (level=error) | Medium | Error information | 90 days |
| **DATA-015** | Admin Sessions | Database Table | `admin_sessions` table | High | Admin access records | 1 year |

---

## Configuration Assets

### Environment Variables

| Asset ID | Asset Name | Type | Location | Classification | Sensitivity |
|----------|------------|------|----------|----------------|-------------|
| **CONF-001** | JWT Secret | Secret | Render env vars | Critical | Authentication secret |
| **CONF-002** | Database URL | Secret | Render env vars | Critical | Database credentials |
| **CONF-003** | Stripe API Keys | Secret | Render env vars | Critical | Payment processing |
| **CONF-004** | Stripe Webhook Secret | Secret | Render env vars | Critical | Webhook verification |
| **CONF-005** | OpenAI API Key | Secret | Render env vars | High | AI service access |
| **CONF-006** | The Odds API Key | Secret | Render env vars | High | Sports data access |
| **CONF-007** | LemonSqueezy Webhook Secret | Secret | Render env vars | High | Webhook verification |
| **CONF-008** | Coinbase Commerce Webhook Secret | Secret | Render env vars | High | Webhook verification |

### Configuration Files

| Asset ID | Asset Name | Type | Location | Classification | Description |
|----------|------------|------|----------|----------------|-------------|
| **CONF-009** | render.yaml | Configuration | Repository root | Critical | Render Blueprint configuration |
| **CONF-010** | .env.example | Configuration | `backend/.env.example` | Low | Example environment variables (no secrets) |

---

## Source Code Assets

| Asset ID | Asset Name | Type | Location | Classification | Description |
|----------|------------|------|----------|----------------|-------------|
| **CODE-001** | GitHub Repository | Source Control | GitHub | Critical | All application code, configuration, documentation |
| **CODE-002** | Backend Code | Source Code | `backend/` | Critical | FastAPI application code |
| **CODE-003** | Frontend Code | Source Code | `frontend/` | Critical | Next.js application code |
| **CODE-004** | Documentation | Documentation | `docs/`, `compliance/` | Medium | Technical and compliance documentation |

---

## Third-Party Service Assets

| Asset ID | Asset Name | Type | Provider | Classification | Data Handled | Access Method |
|----------|------------|------|----------|----------------|--------------|---------------|
| **EXT-001** | Stripe | Payment Processor | Stripe | Critical | Payment data (PCI handled by Stripe) | API, Dashboard |
| **EXT-002** | OpenAI | AI Service | OpenAI | High | User prompts, parlay data | API |
| **EXT-003** | The Odds API | Sports Data | The Odds API | Medium | Sports odds data (read-only) | API |
| **EXT-004** | Render | Infrastructure | Render | Critical | Application hosting, database | Dashboard, API |
| **EXT-005** | GitHub | Source Control | GitHub | Critical | Source code, configuration | Dashboard, Git |
| **EXT-006** | Resend | Email Service | Resend | Medium | Email addresses, email content | API |

---

## Backup Assets

| Asset ID | Asset Name | Type | Location | Classification | Retention |
|----------|------------|------|----------|----------------|-----------|
| **BACKUP-001** | Database Backups | Backup | Render-managed storage | Critical | 7 days (daily) |
| **BACKUP-002** | Code Backups | Backup | GitHub repository | Critical | Permanent (Git history) |
| **BACKUP-003** | Configuration Backups | Backup | Secure document storage | High | 7 years |

---

## Asset Ownership

**Dev Team:** All application and infrastructure assets  
**Render:** Infrastructure hosting and database management  
**Stripe:** Payment processing and PCI compliance  
**GitHub:** Source code repository hosting

---

## Asset Protection

### Encryption
- **In Transit:** HTTPS/TLS for all external communications
- **At Rest:** Render PostgreSQL encrypted at rest (Render-managed)
- **Backups:** Render backups encrypted at rest

### Access Control
- **Application:** Role-based access control (admin/mod/user)
- **Infrastructure:** Render dashboard and GitHub authentication
- **Database:** Render private network access only

### Monitoring
- **Application:** System logs, payment event logs
- **Infrastructure:** Render service health monitoring
- **Access:** Render and GitHub access logs

---

**Last Updated:** 2025-01-XX  
**Next Review:** Quarterly
