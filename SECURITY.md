# Security Policy

## Supported Versions

We actively support security updates for the current production version of Parlay Gorilla.

| Version | Supported          |
| ------- | ------------------ |
| Latest  | :white_check_mark: |
| < Latest| :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

### How to Report

If you discover a security vulnerability, please report it via one of the following methods:

1. **Email (Preferred):** Send details to `security@f3ai.dev`
2. **GitHub Security Advisory:** Use GitHub's private vulnerability reporting feature (if enabled)

### What to Include

Please include the following information in your report:

- **Type of vulnerability** (e.g., XSS, SQL injection, authentication bypass)
- **Affected component** (e.g., authentication, payment processing, API endpoint)
- **Steps to reproduce** (detailed, if possible)
- **Potential impact** (e.g., data exposure, unauthorized access, financial loss)
- **Suggested fix** (if you have one)

### Response Timeline

- **Initial Response:** Within 48 hours
- **Status Update:** Within 7 days
- **Fix Timeline:** Depends on severity (see below)

### Severity Levels

#### 🔴 Critical (Response within 24 hours)
- Remote code execution
- SQL injection leading to data breach
- Authentication bypass
- Payment processing vulnerabilities
- Webhook signature verification bypass
- Secret/token exposure

#### 🟡 High (Response within 7 days)
- Privilege escalation
- Cross-site scripting (XSS)
- CSRF vulnerabilities
- Rate limiting bypass
- Data exposure (non-sensitive)

#### 🟢 Medium (Response within 30 days)
- Information disclosure
- Denial of service (DoS)
- Missing security headers
- Weak encryption/hashing

#### ⚪ Low (Response as time permits)
- Security best practice violations
- Missing security documentation
- Minor configuration issues

## Security Best Practices

### For Developers

1. **Never commit secrets:**
   - API keys
   - Database credentials
   - Webhook secrets
   - JWT secrets
   - Private keys

2. **Use environment variables:**
   - All secrets must be in `.env` (never committed)
   - Use `.env.example` for documentation
   - Never hardcode secrets in code

3. **Validate all inputs:**
   - Use Pydantic models for API validation
   - Sanitize user inputs
   - Validate webhook signatures

4. **Follow secure coding practices:**
   - Use parameterized queries (SQLAlchemy)
   - Implement rate limiting
   - Use HTTPS only in production
   - Store passwords with bcrypt (never plain text)

### For Users

1. **Use strong passwords:**
   - Minimum 6 characters (recommended: 12+)
   - Mix of letters, numbers, symbols
   - Don't reuse passwords

2. **Keep your account secure:**
   - Don't share your account
   - Log out on shared devices
   - Report suspicious activity immediately

3. **Be cautious with links:**
   - Only click links from official sources
   - Verify email addresses before clicking
   - Report phishing attempts

## Security Features

### Authentication & Authorization

- **JWT-based authentication** with secure token storage
- **Bcrypt password hashing** (never plain text)
- **Email verification** required for account activation
- **Role-based access control** (user, mod, admin)
- **Rate limiting** on authentication endpoints

### Payment Security

- **Webhook signature verification** (HMAC-SHA256)
- **Idempotency** to prevent duplicate processing
- **Payment event logging** for audit trails
- **PCI-compliant** payment providers (LemonSqueezy, Coinbase Commerce)

### Data Protection

- **HTTPS only** in production
- **SQL injection prevention** via parameterized queries
- **XSS protection** via input sanitization
- **CORS** properly configured
- **Database encryption** at rest (Render PostgreSQL)

### Infrastructure

- **Render private network** for database access
- **Environment variable** management
- **Secret scanning** (GitHub Secret Scanning enabled)
- **Regular security updates** for dependencies

## Known Security Considerations

### Current Limitations

1. **Token Storage:**
   - JWT tokens stored in localStorage (XSS risk)
   - Consider HttpOnly cookies for production (future improvement)

2. **Rate Limiting:**
   - Rate limiting exists but may need tuning for scale
   - IP-based throttling recommended for auth endpoints

3. **Monitoring:**
   - Security event monitoring could be enhanced
   - Alert system for suspicious activity (future improvement)

## Security Updates

Security updates are released as needed. Critical vulnerabilities are patched immediately.

## Disclosure Policy

- We will acknowledge receipt of your vulnerability report within 48 hours
- We will provide an estimated timeline for a fix
- We will notify you when the vulnerability is fixed
- We will credit you in security advisories (if you wish)

## Contact

For security-related questions or concerns:

- **Email:** security@f3ai.dev
- **Support:** contact@f3ai.dev

---

**Last Updated:** December 2025  
**Version:** 1.0

