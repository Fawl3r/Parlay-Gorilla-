# Routing Structure

## Public Routes (No Authentication Required)

- `/` - **Landing Page** - Marketing page with features, how it works, and signup CTA
- `/build` - **Gorilla Parlay Builder (Public)** - Generate AI parlays without needing the full dashboard
- `/analysis` - **Game Analytics (Public)** - Shareable analysis pages and matchup breakdowns
- `/auth/login` - Login page
- `/auth/signup` - Signup page
- `/auth/callback` - OAuth callback handler
- `/tutorial` - **User Tutorial** - Step-by-step walkthrough with screenshots
- `/docs` - **Documentation** - Quick start + feature guide

## Protected Routes (Authentication Required)

- `/app` - **Main Application** - Parlay builder, games, sports selection
- `/analytics` - User analytics dashboard (shows an auth-required message if not signed in)

## User Flow

1. **New User Journey:**
   - Lands on `/` (public landing page)
   - Clicks "Get Started Free" → `/auth/signup`
   - After signup/email verification → `/profile/setup` → `/app`

2. **Returning User Journey:**
   - Lands on `/` (public landing page)
   - Clicks "Sign In" → `/auth/login`
   - After login → `/app` (or previously intended destination)

3. **Authenticated User:**
   - Can access `/app`, `/analysis`, `/analytics`
   - Header shows user email and "Sign Out" button
   - "Get Started" button redirects to `/app`

## Navigation

- **Public Header:** Shows "Features", "How It Works", "Sign In", "Get Started"
- **Authenticated Header:** Shows "App", "Analysis", "Analytics", user email, "Sign Out"

