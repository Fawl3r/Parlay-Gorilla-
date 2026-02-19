# PARLAY GORILLA V2 UI/UX REDESIGN

## 🎯 Overview

This is a **completely isolated** V2 redesign of the Parlay Gorilla landing page and app UI, inspired by DraftKings' sportsbook aesthetic. The V2 UI is production-safe and can be previewed without any risk to the existing production interface.

## ✅ Safety Guarantees

- **100% Isolated**: All V2 code exists in separate directories (`app/v2/`, `components/v2/`, `lib/v2/`)
- **Zero Production Impact**: No existing routes, components, or styles are modified
- **Easy to Delete**: If rejected, simply delete the V2 folders with zero side effects
- **Namespaced Routes**: All V2 routes are under `/v2` and `/v2/app/*`

## 📂 File Structure

```
frontend/
├── app/v2/                          # V2 routes (isolated)
│   ├── layout.tsx                   # V2 root layout
│   ├── page.tsx                     # V2 landing page
│   ├── v2-styles.css               # V2 custom styles
│   └── app/                         # V2 app routes
│       ├── layout.tsx               # App shell layout
│       ├── page.tsx                 # Dashboard
│       ├── builder/page.tsx         # Parlay builder
│       ├── analytics/page.tsx       # Analytics
│       ├── leaderboard/page.tsx     # Leaderboard
│       └── settings/page.tsx        # Settings
│
├── components/v2/                   # V2 components (isolated)
│   ├── OddsChip.tsx                # Odds display component
│   ├── ConfidenceMeter.tsx         # Confidence indicator
│   ├── SportBadge.tsx              # Sport label
│   ├── GlassCard.tsx               # Glass morphism card
│   ├── PickCard.tsx                # Pick display card
│   ├── app/                         # App-specific components
│   │   ├── V2DesktopSidebar.tsx
│   │   ├── V2MobileNav.tsx
│   │   └── V2TopBar.tsx
│   └── landing/                     # Landing page sections
│       ├── V2HeroSection.tsx
│       ├── V2LivePicksSection.tsx
│       ├── V2HowItWorksSection.tsx
│       ├── V2WhySection.tsx
│       └── V2CtaSection.tsx
│
└── lib/v2/                          # V2 utilities (isolated)
    └── mock-data.ts                 # Mock data for V2 preview
```

## 🚀 Available Routes

### Landing
- `/v2` - V2 landing page

### App
- `/v2/app` - Dashboard (today's picks, stats overview)
- `/v2/app/builder` - Parlay builder with pick selection
- `/v2/app/analytics` - Performance analytics
- `/v2/app/leaderboard` - Rankings and comparisons
- `/v2/app/settings` - Account settings

## 🎨 Design Features

### Visual Style
- **Dark Mode**: Slate-900/950 backgrounds (#0b0e11, #0f172a)
- **Accent Color**: Emerald green (#22c55e) for CTAs and positive indicators
- **Card Style**: Glass morphism with backdrop blur
- **Typography**: Bold, readable, sportsbook-grade

### UI Patterns
- ✅ Odds chips with positive/negative variants
- ✅ Confidence meters with color-coded thresholds
- ✅ Sport badges with unique colors per league
- ✅ Glass cards with hover effects
- ✅ Desktop sidebar navigation
- ✅ Mobile bottom tab bar
- ✅ Sticky headers
- ✅ Horizontal scroll carousels

### Responsive Design
- ✅ Mobile-first approach
- ✅ Bottom navigation on mobile (< 1024px)
- ✅ Sidebar navigation on desktop (≥ 1024px)
- ✅ Touch targets ≥ 44px
- ✅ No horizontal page scrolling
- ✅ Smooth transitions (200ms default)

## 🧪 Mock Data

All V2 pages use mock data from `lib/v2/mock-data.ts`:
- Mock picks (NFL, NBA, NHL, MLB, etc.)
- Mock leaderboard entries
- Mock analytics data
- Helper functions for formatting

**No production APIs are connected yet.**

## 🔧 Tech Stack

- **Framework**: Next.js 14 App Router
- **Styling**: Tailwind CSS (existing config)
- **Language**: TypeScript
- **State**: React hooks (local state only)
- **No new dependencies added**

## 📱 Screenshots / Preview

To preview the V2 UI:
1. Start the dev server: `npm run dev` (in `frontend/`)
2. Navigate to `http://localhost:3000/v2`
3. Explore:
   - Landing page: `/v2`
   - Dashboard: `/v2/app`
   - Builder: `/v2/app/builder`
   - Analytics: `/v2/app/analytics`
   - Leaderboard: `/v2/app/leaderboard`
   - Settings: `/v2/app/settings`

## 🛡️ Production Safety Checklist

- [x] All V2 code is in isolated directories
- [x] No modifications to existing production files
- [x] No changes to existing routes (`/`, `/app`, etc.)
- [x] No shared components modified
- [x] No global styles overridden
- [x] V2 layout prevents context contamination
- [x] Uses only mock data (no production API calls)
- [x] Can be deleted with zero side effects

## 🗑️ How to Remove V2 (If Rejected)

If the V2 design is not approved, simply delete these folders:

```bash
# From frontend directory
rm -rf app/v2
rm -rf components/v2
rm -rf lib/v2
```

**That's it.** No cleanup, no migrations, no rollbacks needed.

## 🔄 Next Steps (If Approved)

1. **User Testing**: Gather feedback on V2 design
2. **Data Integration**: Replace mock data with real API calls
3. **Feature Parity**: Ensure all production features work in V2
4. **Migration Plan**: Create a gradual rollout strategy
5. **Deprecation**: Phase out V1 UI after V2 is stable

## 📝 Notes

- V2 uses the existing Tailwind config (no theme overrides)
- V2 respects the existing emerald/logo-green color system
- All components are "use client" for interactivity
- Mobile nav has 44px+ tap targets for accessibility
- Confidence thresholds: 75%+ (green), 65-74% (yellow), <65% (orange)

## 👨‍💻 Development

To extend V2:
1. Add new pages in `app/v2/app/[page]/page.tsx`
2. Create reusable components in `components/v2/`
3. Add utilities/helpers in `lib/v2/`
4. Keep everything isolated from production code

---

**Built with zero impact on production. Preview safely. Delete easily.**
