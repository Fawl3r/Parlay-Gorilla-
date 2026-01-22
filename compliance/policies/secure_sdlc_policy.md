# Secure Software Development Lifecycle (SDLC) Policy

**Policy ID:** SDLC-001  
**Version:** 1.0  
**Effective Date:** 2025-01-XX  
**Review Frequency:** Quarterly  
**Owner:** Development Team

---

## 1. Purpose

This policy defines security requirements and practices for the software development lifecycle (SDLC) of Parlay Gorilla, ensuring that security is integrated into all phases of development.

---

## 2. Scope

This policy applies to:
- **Application Development:** Frontend (Next.js), Backend (FastAPI)
- **Database Development:** Schema changes, migrations
- **Infrastructure:** Render configuration, environment variables
- **Third-Party Integrations:** API integrations, webhook implementations

---

## 3. SDLC Phases

### 3.1 Planning and Requirements

**Security Requirements:**
- Identify security requirements for new features
- Assess data sensitivity and classification
- Define authentication/authorization requirements
- Plan security testing approach

**Deliverables:**
- Security requirements document
- Threat model (for complex features)
- Data flow diagrams (if applicable)

### 3.2 Design

**Security Design:**
- Authentication/authorization design
- Data encryption requirements
- Input validation strategy
- Error handling (no information leakage)
- Logging and monitoring requirements

**Design Review:**
- Security-focused design review
- Threat modeling (for high-risk features)
- Architecture review

### 3.3 Development

**Secure Coding Practices:**
- Input validation on all user inputs
- Parameterized queries (SQL injection prevention)
- Output encoding (XSS prevention)
- Authentication checks on all protected endpoints
- Error handling (generic error messages)

**Code Standards:**
- Follow existing code patterns
- Security-focused code review
- No hardcoded secrets
- Environment variables for configuration

**Implementation:**
- **Backend:** `backend/app/` - FastAPI application
- **Frontend:** `frontend/app/` - Next.js application
- **Database:** Alembic migrations in `backend/alembic/versions/`

### 3.4 Testing

**Security Testing:**
- Unit tests for security functions
- Integration tests for authentication/authorization
- Input validation testing
- Error handling testing

**Test Types:**
- **Unit Tests:** `backend/tests/` - Python pytest tests
- **Integration Tests:** API endpoint tests
- **Security Tests:** Authentication, authorization, input validation

**Test Requirements:**
- All security-critical code must have tests
- Tests must cover positive and negative cases
- Tests must verify error handling

### 3.5 Deployment

**Deployment Security:**
- Secrets managed via Render environment variables
- No secrets in code or repository
- Database migrations tested before production
- Deployment via Render automatic deploys

**Deployment Process:**
1. Code merged to main branch
2. Render automatically deploys
3. Database migrations run automatically (via `start.sh`)
4. Health checks verify deployment
5. Monitor for errors

**Deployment Files:**
- `render.yaml` - Render Blueprint configuration
- `backend/start.sh` - Startup script (runs migrations)

### 3.6 Maintenance

**Security Maintenance:**
- Regular dependency updates
- Security patch application
- Vulnerability remediation
- Security monitoring

---

## 4. Security Requirements

### 4.1 Authentication and Authorization

**Requirements:**
- All protected endpoints require authentication
- Role-based access control (admin/mod/user)
- JWT token validation on all protected routes
- Password hashing (PBKDF2-SHA256)

**Implementation:**
- **Backend:** `backend/app/core/dependencies.py` - `get_current_user()`
- **Admin:** `backend/app/api/routes/admin/auth.py` - `require_admin()`

### 4.2 Input Validation

**Requirements:**
- Validate all user inputs
- Sanitize inputs before processing
- Reject invalid inputs with clear error messages
- No SQL injection vulnerabilities

**Implementation:**
- **Backend:** Pydantic models for request validation
- **Database:** SQLAlchemy ORM (parameterized queries)

**Example:**
```python
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
```

### 4.3 Output Encoding

**Requirements:**
- Encode all user-generated content
- Prevent XSS attacks
- Sanitize data before display

**Implementation:**
- **Frontend:** React automatic escaping
- **Backend:** JSON responses (no HTML rendering)

### 4.4 Error Handling

**Requirements:**
- Generic error messages (no information leakage)
- Log detailed errors server-side
- No stack traces in production responses

**Implementation:**
- **Backend:** FastAPI exception handlers
- **Logging:** `system_logs` table for error tracking

### 4.5 Secrets Management

**Requirements:**
- No secrets in code or repository
- Secrets stored in Render environment variables
- Secrets rotated periodically

**Implementation:**
- **Configuration:** `backend/app/core/config.py` - Pydantic Settings
- **Storage:** Render dashboard environment variables

### 4.6 Logging and Monitoring

**Requirements:**
- Log security events (authentication, authorization failures)
- Log admin actions
- Log payment events
- Monitor for suspicious activity

**Implementation:**
- **System Logs:** `backend/app/models/system_log.py`
- **Payment Events:** `backend/app/models/payment_event.py`

---

## 5. Code Review Process

### 5.1 Review Requirements

**All Code Changes:**
- Security-focused code review
- Review for vulnerabilities
- Verify security requirements met
- Approve before merging

**Review Checklist:**
- [ ] Input validation implemented
- [ ] Authentication/authorization checks present
- [ ] No secrets in code
- [ ] Error handling appropriate
- [ ] Logging implemented (if applicable)
- [ ] Tests written and passing

### 5.2 Review Process

**Process:**
1. Create pull request
2. Code review (self-review acceptable for solo developer)
3. Security review
4. Approve and merge

**Review Tools:**
- GitHub pull requests
- Manual code review
- Automated tests (pytest, vitest)

---

## 6. Security Testing

### 6.1 Testing Types

**Unit Tests:**
- Test security functions (password hashing, token generation)
- Test input validation
- Test error handling

**Integration Tests:**
- Test authentication flows
- Test authorization checks
- Test API endpoints

**Security Tests:**
- Test for common vulnerabilities (SQL injection, XSS)
- Test authentication bypass attempts
- Test authorization bypass attempts

### 6.2 Testing Requirements

**Coverage:**
- All security-critical code must have tests
- Tests must cover positive and negative cases
- Tests must verify error handling

**Test Locations:**
- **Backend:** `backend/tests/`
- **Frontend:** `frontend/tests/` (if applicable)

---

## 7. Dependency Management

### 7.1 Dependency Security

**Requirements:**
- Regular dependency updates
- Vulnerability scanning
- Security patch application

**Tools:**
- **GitHub Dependabot:** Automatic vulnerability alerts
- **Manual Audits:** Quarterly dependency reviews

**Update Process:**
1. Review vulnerability details
2. Check for compatible updates
3. Update dependencies
4. Test changes
5. Deploy

### 7.2 Dependency Files

**Backend:**
- `backend/requirements.txt` - Python dependencies

**Frontend:**
- `frontend/package.json` - Node dependencies

---

## 8. Secure Configuration

### 8.1 Configuration Security

**Requirements:**
- No default passwords
- Secure default settings
- Configuration validation
- Secrets in environment variables

**Implementation:**
- **Backend:** `backend/app/core/config.py` - Pydantic Settings with validation
- **Frontend:** Environment variables (NEXT_PUBLIC_*)

### 8.2 Environment Separation

**Environments:**
- **Development:** Local environment, test data
- **Production:** Render production, real data

**Separation:**
- Different database instances
- Different API keys (test vs production)
- Different configuration values

---

## 9. Incident Response in Development

### 9.1 Security Incident Response

**Process:**
1. Identify vulnerability
2. Assess severity
3. Develop fix
4. Test fix
5. Deploy fix
6. Document incident

**See:** `incident_response_plan.md` for detailed procedures

---

## 10. Training and Awareness

### 10.1 Developer Training

**Topics:**
- Secure coding practices
- Common vulnerabilities (OWASP Top 10)
- Authentication/authorization best practices
- Secrets management

**Frequency:** Annually or when new developers join

---

## 11. Compliance

This policy supports SOC 2 Type I readiness under **Security Trust Service Criteria CC8.1** (Change management process).

---

## 12. Policy Review

This policy is reviewed quarterly or when:
- Development processes change
- New security requirements identified
- Significant security incidents occur

---

**Approved By:** [To be filled]  
**Last Review Date:** [To be filled]  
**Next Review Date:** [To be filled]
