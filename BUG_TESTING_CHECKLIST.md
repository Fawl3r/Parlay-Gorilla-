# Bug Testing Checklist for www.parlaygorilla.com

## Critical Bugs Found

### 1. ✅ FIXED: Missing 500 Error Handler in Frontend
- **Location**: `frontend/lib/api/services/ParlayApi.ts`
- **Issue**: 500 errors from `/api/parlay/suggest` were not being handled gracefully
- **Fix**: Added specific 500 error handler with user-friendly message
- **Status**: Fixed

### 2. 🔍 INVESTIGATING: 500 Error on `/api/parlay/suggest`
- **Location**: `backend/app/api/routes/parlay.py`
- **Issue**: Production endpoint returning 500 Internal Server Error
- **Status**: Enhanced error logging added, needs production log analysis
- **Next Steps**: Check Render logs after deployment

## Testing Checklist

### Authentication & User Flow
- [ ] **Landing Page** (`/`)
  - [ ] Page loads without errors
  - [ ] All sections render correctly (Hero, Stats, Features, How It Works, CTA)
  - [ ] Navigation links work
  - [ ] "Get Started" button redirects correctly
  - [ ] "Sign In" button works

- [ ] **Sign Up Flow** (`/auth/signup`)
  - [ ] Form validation works
  - [ ] Email validation
  - [ ] Password requirements enforced
  - [ ] Successful signup redirects correctly
  - [ ] Error messages display properly

- [ ] **Login Flow** (`/auth/login`)
  - [ ] Valid credentials log in successfully
  - [ ] Invalid credentials show error
  - [ ] "Forgot Password" link works
  - [ ] OAuth login (if available) works

- [ ] **Profile Setup** (`/profile/setup`)
  - [ ] Required fields validated
  - [ ] Form submission works
  - [ ] Redirects to `/app` after completion

### Core Features

- [ ] **AI Parlay Builder** (`/app` or `/build`)
  - [ ] Page loads without errors
  - [ ] Sport selection works
  - [ ] Number of legs selector works
  - [ ] Risk profile selector works
  - [ ] **CRITICAL**: Generate parlay button works (currently has 500 error)
  - [ ] Error messages display correctly for:
    - Timeout errors
    - Server errors (500)
    - Validation errors (422)
    - Paywall errors (402)
  - [ ] Loading states display correctly
  - [ ] Generated parlay displays correctly
  - [ ] Save parlay functionality works
  - [ ] Triple parlay mode works

- [ ] **Game Analysis** (`/analysis`)
  - [ ] Game list loads
  - [ ] Individual game analysis pages load
  - [ ] 404 errors handled gracefully
  - [ ] Network errors handled gracefully
  - [ ] Timeout errors handled

- [ ] **Custom Parlay Builder**
  - [ ] Pick selection works
  - [ ] Analysis button works
  - [ ] Save functionality works
  - [ ] Paywall errors handled

### Edge Cases & Error Handling

- [ ] **Network Errors**
  - [ ] Offline state handled
  - [ ] Timeout errors show user-friendly messages
  - [ ] Connection errors don't crash the app

- [ ] **API Errors**
  - [ ] 400 Bad Request handled
  - [ ] 401 Unauthorized redirects to login
  - [ ] 403 Forbidden shows appropriate message
  - [ ] 404 Not Found handled
  - [ ] 422 Validation errors show field-specific messages
  - [ ] **500 Internal Server Error** - Currently broken, needs fix
  - [ ] 502/503/504 errors handled

- [ ] **Empty States**
  - [ ] No games available
  - [ ] No parlays generated
  - [ ] No saved parlays

### Payment & Billing

- [ ] **Pricing Page** (`/pricing`)
  - [ ] Plans display correctly
  - [ ] Purchase buttons work
  - [ ] Payment flow works

- [ ] **Billing Page** (`/billing`)
  - [ ] Subscription status displays
  - [ ] Payment methods display
  - [ ] Update payment method works

### Mobile Responsiveness

- [ ] **Mobile View** (< 768px)
  - [ ] Navigation works
  - [ ] Forms are usable
  - [ ] Buttons are tappable
  - [ ] Text is readable
  - [ ] Images scale correctly

- [ ] **Tablet View** (768px - 1024px)
  - [ ] Layout adapts correctly
  - [ ] All features accessible

### Performance

- [ ] **Page Load Times**
  - [ ] Landing page < 3s
  - [ ] App dashboard < 2s
  - [ ] API responses < 5s

- [ ] **Caching**
  - [ ] Parlay suggestions cached correctly
  - [ ] Cache invalidation works

### Security

- [ ] **Authentication**
  - [ ] JWT tokens validated
  - [ ] Expired tokens handled
  - [ ] Invalid tokens rejected

- [ ] **Authorization**
  - [ ] Protected routes require auth
  - [ ] Admin routes protected
  - [ ] User data isolated

## Known Issues to Test

1. **500 Error on Parlay Generation**
   - Test: Try generating a parlay
   - Expected: Should work after backend fix
   - Current: Returns 500 error

2. **Error Message Display**
   - Test: Trigger various errors
   - Expected: User-friendly messages
   - Current: Some errors may show technical details

## Testing Tools

- Browser DevTools (Console, Network tab)
- Render Dashboard (for backend logs)
- Postman/curl (for API testing)

## Priority Fixes

1. **HIGH**: Fix 500 error on `/api/parlay/suggest` (in progress)
2. **HIGH**: Improve error handling for 500 errors in frontend (fixed)
3. **MEDIUM**: Add better error messages for all API errors
4. **MEDIUM**: Add retry logic for transient errors


