# Dashboard Testing Plan

## Dashboard Overview

The Parlay Gorilla dashboard (`/app`) has 4 main tabs:
1. **Games** - View upcoming games by sport and date
2. **AI Picks** - Generate AI-powered parlay suggestions
3. **Gorilla Parlay Builder** - Build custom parlays with manual picks
4. **Insights** - View analytics and performance metrics

## Test Checklist

### 1. Dashboard Load & Authentication

- [ ] Dashboard loads without errors
- [ ] ProtectedRoute redirects unauthenticated users
- [ ] Header displays correctly
- [ ] BalanceStrip shows credits and usage
- [ ] DashboardAccountCommandCenter displays
- [ ] All tabs are visible and clickable
- [ ] Default tab is "Games"

### 2. Games Tab

- [ ] Games tab loads
- [ ] Sport selector works (NFL, NBA, NHL, MLB, NCAAF, NCAAB, EPL, MLS)
- [ ] Date navigation works (today, prev, next)
- [ ] Games list loads for selected sport/date
- [ ] Market filter works (all, h2h, spreads, totals)
- [ ] Game rows display correctly
- [ ] Win probability shows (if premium or authenticated)
- [ ] "Add to Parlay" functionality
- [ ] Loading states display correctly
- [ ] Error states display correctly
- [ ] Refresh button works

### 3. AI Picks Tab

- [ ] AI Picks tab loads
- [ ] ParlayBuilder component renders
- [ ] Sport selection works
- [ ] Number of legs selector works
- [ ] Risk profile selector works (safe, balanced, degen)
- [ ] Week selector works (for NFL)
- [ ] Mix sports toggle works
- [ ] Generate button works
- [ ] **CRITICAL**: Test parlay generation (currently has 500 error)
- [ ] Loading states display
- [ ] Error messages display correctly
- [ ] Generated parlay displays
- [ ] Save parlay works
- [ ] Triple parlay mode works

### 4. Gorilla Parlay Builder Tab

- [ ] Custom builder tab loads
- [ ] Can select games
- [ ] Can select picks
- [ ] Can add legs to parlay
- [ ] Can remove legs
- [ ] Analyze button works
- [ ] Save button works
- [ ] Paywall errors handled correctly
- [ ] Analysis results display

### 5. Insights Tab

- [ ] Analytics tab loads
- [ ] Analytics component renders
- [ ] Stats display correctly
- [ ] Charts/graphs render
- [ ] No console errors

### 6. Dashboard Components

#### BalanceStrip
- [ ] Credits display correctly
- [ ] Usage limits display correctly
- [ ] Premium vs free display correctly
- [ ] Links to pricing work

#### DashboardAccountCommandCenter
- [ ] Usage gauges display
- [ ] Stats load correctly
- [ ] Coach insights display
- [ ] Quick action buttons work

### 7. Navigation & State

- [ ] Tab switching works smoothly
- [ ] Active tab indicator works
- [ ] URL params update on tab change
- [ ] Browser back/forward works
- [ ] State persists on refresh
- [ ] No redirect loops

### 8. Error Handling

- [ ] Network errors handled gracefully
- [ ] 401 errors redirect to login
- [ ] 500 errors show user-friendly messages
- [ ] Timeout errors handled
- [ ] Empty states display correctly

### 9. Mobile Responsiveness

- [ ] Dashboard works on mobile
- [ ] Tabs scroll horizontally on mobile
- [ ] Sport selector is dropdown on mobile
- [ ] All features accessible on mobile

### 10. Performance

- [ ] Dashboard loads quickly
- [ ] Tab switching is smooth
- [ ] No excessive re-renders
- [ ] API calls are efficient

## Known Issues to Test

1. **500 Error on AI Picks Generation**
   - Test: Try generating a parlay
   - Expected: Should work after backend fix
   - Current: Returns 500 error

2. **Profile Completion Redirect**
   - Test: Access dashboard with incomplete profile
   - Expected: Redirects to profile setup
   - Current: Should work correctly

## Priority Test Areas

1. **HIGH**: AI Picks parlay generation (500 error)
2. **HIGH**: Dashboard load and authentication
3. **HIGH**: Tab navigation
4. **MEDIUM**: Games tab functionality
5. **MEDIUM**: Custom builder functionality
6. **LOW**: UI polish and animations

## Test Data Needed

- Valid user account (free and premium)
- Games data available
- API endpoints working
- Database populated


