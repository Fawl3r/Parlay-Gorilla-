# Complete Account Creation Test Plan

## Flow Overview

1. **Signup** (`/auth/signup`)
   - Email input
   - Password input (min 6 chars)
   - Confirm password
   - Form validation
   - API call to `/api/auth/register`
   - Token storage
   - Redirect logic

2. **Profile Setup** (`/profile/setup`)
   - Step 1: Display name (required)
   - Step 2: Favorite sports (optional)
   - Step 3: Favorite teams (optional)
   - Step 4: Betting style (default: balanced)
   - API call to `/api/profile/setup`
   - Profile completion verification
   - Redirect to `/app`

3. **App Access** (`/app`)
   - Verify user can access main app
   - Verify profile data is available

## Test Cases

### 1. Signup Page Tests

#### 1.1 Valid Signup
- [ ] Enter valid email (e.g., `test@example.com`)
- [ ] Enter password (6+ characters)
- [ ] Confirm password matches
- [ ] Click "Create Account"
- [ ] Verify loading state shows
- [ ] Verify success message or redirect
- [ ] Verify token is stored
- [ ] Verify user is authenticated

#### 1.2 Form Validation
- [ ] Empty email shows validation error
- [ ] Invalid email format shows error
- [ ] Password < 6 characters shows error
- [ ] Password mismatch shows error
- [ ] All fields required

#### 1.3 Error Handling
- [ ] Duplicate email shows appropriate error
- [ ] Network error shows user-friendly message
- [ ] 500 error shows user-friendly message
- [ ] Timeout error shows user-friendly message
- [ ] Rate limiting shows appropriate message

#### 1.4 Edge Cases
- [ ] Email with uppercase letters (should normalize)
- [ ] Very long email
- [ ] Very long password (72 char limit)
- [ ] Special characters in email
- [ ] Special characters in password

### 2. Profile Setup Tests

#### 2.1 Complete Flow
- [ ] Redirects to `/profile/setup` after signup
- [ ] Step 1: Enter display name
- [ ] Step 2: Select sports (optional)
- [ ] Step 3: Select teams (optional)
- [ ] Step 4: Select betting style
- [ ] Click "Complete Setup"
- [ ] Verify loading state
- [ ] Verify profile is saved
- [ ] Verify redirect to `/app`

#### 2.2 Validation
- [ ] Display name is required
- [ ] Can proceed without sports
- [ ] Can proceed without teams
- [ ] Betting style has default value
- [ ] Can go back to previous steps
- [ ] Progress bar updates correctly

#### 2.3 Error Handling
- [ ] Network error shows error message
- [ ] 500 error shows error message
- [ ] Invalid data shows validation error
- [ ] Profile completion verification failure shows error

#### 2.4 Edge Cases
- [ ] Very long display name (50 char limit)
- [ ] Many sports selected
- [ ] Many teams selected
- [ ] Empty display name (should fail)
- [ ] Whitespace-only display name (should fail)

### 3. Integration Tests

#### 3.1 Full Flow
- [ ] Signup → Profile Setup → App Access
- [ ] Verify user data persists
- [ ] Verify profile_completed flag is set
- [ ] Verify badges are awarded
- [ ] Verify redirects work correctly

#### 3.2 Authentication State
- [ ] User stays logged in after signup
- [ ] Token persists across page refreshes
- [ ] Cookie is set correctly
- [ ] Can access protected routes

#### 3.3 Profile Data
- [ ] Display name is saved
- [ ] Favorite sports are saved
- [ ] Favorite teams are saved
- [ ] Betting style is saved
- [ ] Data appears in profile page

### 4. Backend Tests

#### 4.1 Registration Endpoint
- [ ] Valid registration returns 200
- [ ] Returns access token
- [ ] Returns user data
- [ ] Sets HttpOnly cookie
- [ ] Creates user in database
- [ ] Normalizes email
- [ ] Hashes password correctly
- [ ] Allocates account number

#### 4.2 Error Cases
- [ ] Duplicate email returns 400
- [ ] Invalid email returns 422
- [ ] Password too short returns 422
- [ ] Password too long returns 400
- [ ] Rate limiting works (5/minute)
- [ ] Timeout handling works

#### 4.3 Profile Setup Endpoint
- [ ] Valid setup returns 200
- [ ] Sets profile_completed = True
- [ ] Saves all profile fields
- [ ] Awards "profile-complete" badge
- [ ] Returns updated user data

#### 4.4 Error Cases
- [ ] Missing display_name returns 400
- [ ] Invalid user returns 404
- [ ] Unauthenticated returns 401
- [ ] Invalid data returns 400

## Known Issues to Test

1. **Profile Completion Verification**
   - Issue: Frontend retries up to 10 times to verify profile completion
   - Test: Verify this works correctly
   - Test: Verify error handling if verification fails

2. **Redirect Loops**
   - Issue: Potential redirect loop if profile_completed flag not set correctly
   - Test: Verify no redirect loops occur
   - Test: Verify redirect logic works correctly

3. **Email Verification**
   - Issue: Email verification is optional (non-blocking)
   - Test: Verify signup works without email verification
   - Test: Verify email verification flow if enabled

## Testing Checklist

### Pre-Test Setup
- [ ] Clear browser cache
- [ ] Clear cookies
- [ ] Use incognito/private window
- [ ] Check browser console for errors
- [ ] Check network tab for failed requests

### During Test
- [ ] Monitor browser console
- [ ] Monitor network requests
- [ ] Check response status codes
- [ ] Verify error messages are user-friendly
- [ ] Verify loading states work
- [ ] Verify redirects work correctly

### Post-Test
- [ ] Verify user created in database
- [ ] Verify profile data saved correctly
- [ ] Verify profile_completed flag is True
- [ ] Verify badges awarded
- [ ] Verify token works for subsequent requests

## Bug Report Template

```
**Bug Title**: [Brief description]

**Steps to Reproduce**:
1. 
2. 
3. 

**Expected Behavior**:
[What should happen]

**Actual Behavior**:
[What actually happens]

**Error Messages**:
[Any error messages shown]

**Console Errors**:
[Any JavaScript errors]

**Network Errors**:
[Any failed API calls]

**Browser/Device**:
[Browser, version, device]

**Screenshots**:
[If applicable]
```

## Priority Test Areas

1. **HIGH**: Signup form validation
2. **HIGH**: Profile setup completion
3. **HIGH**: Redirect logic
4. **MEDIUM**: Error handling
5. **MEDIUM**: Edge cases
6. **LOW**: UI polish


