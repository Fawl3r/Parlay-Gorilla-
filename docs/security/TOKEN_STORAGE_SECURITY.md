# Token Storage Security Review

**Date:** December 2025  
**Status:** Review Complete - Recommendations Provided

---

## Current Implementation

### Token Storage Location
JWT tokens are currently stored in `localStorage`:

**File:** `frontend/lib/auth/session-manager.ts`

```typescript
class AuthTokenStorage {
  private readonly key = 'auth_token'

  getToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem(this.key)
  }

  setToken(token: string | null) {
    if (typeof window === 'undefined') return
    if (token) {
      localStorage.setItem(this.key, token)
      return
    }
    localStorage.removeItem(this.key)
  }
}
```

---

## Security Considerations

### ⚠️ Current Risk: XSS Vulnerability

**Issue:** Storing JWT tokens in `localStorage` makes them accessible to JavaScript, which means:
- Any XSS (Cross-Site Scripting) vulnerability can steal tokens
- Malicious scripts injected into the page can read `localStorage`
- Tokens persist even after browser close (until explicitly cleared)

### ✅ Mitigations Currently in Place

1. **Token Expiration:** JWT tokens have expiration times
2. **HTTPS Only:** Production uses HTTPS (tokens encrypted in transit)
3. **No Sensitive Data in Token:** JWT payload contains only user ID and basic claims
4. **Token Validation:** Backend validates token signature and expiration

---

## Recommended Improvements

### Option 1: HttpOnly Cookies (Recommended for Production)

**Benefits:**
- Not accessible to JavaScript (XSS protection)
- Automatically sent with requests
- Can be marked `Secure` and `SameSite`

**Implementation Requirements:**
1. Backend must set cookies via `Set-Cookie` header
2. Frontend must send credentials with requests
3. CORS must allow credentials
4. Cookies must be `HttpOnly`, `Secure`, and `SameSite=Strict`

**Trade-offs:**
- More complex implementation
- Requires backend changes
- May need CSRF protection
- Mobile app compatibility considerations

### Option 2: Hybrid Approach (Current + Enhanced)

**Keep localStorage but add:**
1. **Token Refresh:** Implement refresh tokens stored in HttpOnly cookies
2. **Short-lived Access Tokens:** Reduce JWT expiration time (e.g., 15 minutes)
3. **Automatic Refresh:** Refresh tokens before expiration
4. **Content Security Policy (CSP):** Strict CSP headers to prevent XSS

### Option 3: Session Storage (Short-term)

**Benefits:**
- Tokens cleared when tab closes
- Still vulnerable to XSS but less persistent

**Trade-offs:**
- Users must re-authenticate on new tabs
- Still accessible to JavaScript

---

## Implementation Priority

### High Priority (If XSS vulnerabilities exist)
1. Implement HttpOnly cookies
2. Add CSRF protection
3. Implement token refresh mechanism

### Medium Priority (Defense in depth)
1. Reduce JWT expiration time
2. Implement automatic token refresh
3. Add Content Security Policy headers
4. Regular security audits for XSS vulnerabilities

### Low Priority (Nice to have)
1. Session storage as alternative
2. Token encryption at rest (browser storage)
3. Biometric authentication for mobile

---

## Current Security Posture

### ✅ Strengths
- HTTPS enforced in production
- Token expiration implemented
- Backend validates all tokens
- No sensitive data in JWT payload

### ⚠️ Areas for Improvement
- Token storage method (localStorage vs HttpOnly cookies)
- Token refresh mechanism (currently single JWT)
- XSS protection (CSP headers)

---

## Recommendation

**For Production:**
1. **Short-term:** Keep current implementation but add:
   - Strict Content Security Policy
   - Regular XSS vulnerability scanning
   - Token expiration monitoring

2. **Long-term:** Migrate to HttpOnly cookies with:
   - Refresh token in HttpOnly cookie
   - Short-lived access tokens (15-30 minutes)
   - Automatic token refresh
   - CSRF protection

**For Development:**
- Current localStorage approach is acceptable
- Focus on preventing XSS vulnerabilities
- Regular security audits

---

## December 2025 Update: Hybrid Cookie + Bearer Support

The backend now supports a **hybrid** approach:

- The API still returns `access_token` in JSON for existing clients (bearer token flow).
- The API also sets an **HttpOnly** `access_token` cookie on `/api/auth/login` and `/api/auth/register`.
- The API accepts authentication via:
  - `Authorization: Bearer <token>` header, or
  - the `access_token` cookie (when present).

This keeps the current frontend behavior working while enabling a gradual migration away from `localStorage` in production.

---

## Related Files

- `frontend/lib/auth/session-manager.ts` - Token storage implementation
- `frontend/lib/auth-context.tsx` - Authentication context
- `backend/app/api/routes/auth.py` - Token generation
- `backend/app/core/dependencies.py` - Token validation

---

## References

- [OWASP JWT Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)
- [OWASP XSS Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [MDN: HttpOnly Cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies#restrict_access_to_cookies)

