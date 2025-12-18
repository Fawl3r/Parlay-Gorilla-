---
name: Fix Profile Setup Redirect Loop
overview: Fix the redirect loop where users are sent back to profile setup after completing it. The issue is a race condition in the auth context's redirect logic that doesn't properly wait for user state updates.
todos: []
---

# Fix Profile Setup Redirect Loop

## Problem Analysis

The issue occurs in [`frontend/lib/auth-context.tsx`](frontend/lib/auth-context.tsx) where a `useEffect` hook (lines 132-144) redirects users to `/profile/setup` if `!user.profile_completed`. This creates a redirect loop because:

1. **Race Condition**: When profile setup completes, `refreshUser()` is called, then `router.push("/app")` navigates. The pathname change triggers the `useEffect` again before the user state fully updates with `profile_completed: true`.

2. **Timing Issue**: The redirect check doesn't account for the fact that the user is in the process of completing setup or that the state update might be in-flight.

3. **Missing Guard**: There's no protection against redirect loops when the user state is being refreshed.

## Solution

### 1. Fix Auth Context Redirect Logic

**File**: [`frontend/lib/auth-context.tsx`](frontend/lib/auth-context.tsx)

- Add a ref to track if we're currently redirecting to prevent loops
- Add a check to ensure user state is fully loaded before redirecting
- Improve the redirect condition to be more defensive
- Add a small delay or state stability check before redirecting

**Changes**:

- Add `useRef` to track redirect state
- Modify the `useEffect` at lines 132-144 to:
- Check if we're already on `/profile/setup` (prevent redirect loops)
- Wait for loading to complete
- Ensure user state is stable before checking
- Only redirect if user exists and profile is not completed AND we're not already on setup page

### 2. Improve Profile Setup Completion Flow

**File**: [`frontend/app/profile/setup/page.tsx`](frontend/app/profile/setup/page.tsx)

- Ensure `refreshUser()` completes and state is updated before redirecting
- Add a small delay or wait for state to stabilize after `refreshUser()`
- Verify the user state has `profile_completed: true` before redirecting

**Changes**:

- In `handleSubmit` (lines 95-122), after `refreshUser()`:
- Wait for the user state to update with `profile_completed: true`
- Add a verification check before redirecting
- Use `router.replace()` instead of `router.push()` to prevent back navigation issues

### 3. Fix Sign In Redirect Logic

**File**: [`frontend/lib/auth-context.tsx`](frontend/lib/auth-context.tsx)

- In `signIn` function (lines 146-167), ensure we check the backend user data, not just Supabase metadata
- The check at line 158 uses `data.session.user.user_metadata?.profile_completed` which might be out of sync
- Should wait for `syncFromSession` to complete and check the merged backend user data instead

**Changes**:

- After `syncFromSession(data.session)`, check the updated `user` state from backend
- Remove the Supabase metadata check and rely on backend user data

## Implementation Details

1. **Add redirect guard in auth-context**:

- Use `useRef` to track if redirect is in progress
- Check current pathname before redirecting
- Ensure loading is false and user state is stable

2. **Improve profile setup completion**:

- Wait for user state update after `refreshUser()`
- Verify `profile_completed` is true before redirecting
- Use `router.replace()` to prevent history issues

3. **Fix sign-in flow**:

- Wait for backend user sync before checking profile completion
- Use merged user data instead of Supabase metadata

## Testing Checklist

- [ ] Complete profile setup → should redirect to `/app` and stay there
- [ ] Login with completed profile → should go to `/app`, not `/profile/setup`
- [ ] Login with incomplete profile → should go to `/profile/setup`
- [ ] Navigate to `/app` after completing setup → should not redirect back to setup
- [ ] Refresh page after completing setup → should not redirect to setup