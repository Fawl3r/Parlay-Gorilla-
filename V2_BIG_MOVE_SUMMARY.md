# V2 “BIG MOVE” — IMPLEMENTATION SUMMARY

## Objective

V2 was updated to **match V1 brand/vibe** (colors, transparency, glass, imagery) and then **upgraded to an edgy, non-bubble, sportsbook/trading-terminal** feel. V2 reads as “V1 evolved,” not a different product.

---

## Phase 1 — V1 Design Snapshot in V2

### Created
- **`frontend/lib/v2/theme.ts`**  
  Central tokens: `bg0` (#0A0F0A), `bg1` (#121212), `surface` (glass rgba), `border`, `textPrimary`, `textMuted`, `accent` (#00FF5E), `accentFill`, `accentHighlight`, overlays, blur, **V2 sharp radii** (4–6px, no full rounding).

- **`frontend/styles/v2.css`**  
  V2-only base styles. Exports CSS custom properties for the same tokens. Imported **only** by `frontend/app/v2/layout.tsx`. Scoped to `.v2-isolated-ui` so it does not affect V1 or global app.

### Updated
- **`frontend/app/v2/layout.tsx`**  
  Imports `@/styles/v2.css` (plus existing `v2-styles.css` and `animations.css`).

---

## Phase 2 — Edgy / Non-Bubble Upgrade

### Shape language
- **No circles or pills:** no round avatars, no pill tabs, no bubble chips.
- **Sharp geometry:** corners 4–6px (`rounded`, `rounded-md`). Vertical accent bars, thin borders, rectangular badges.
- **Leaderboard:** rank number + username only (no avatars). Segmented Daily/Weekly/Monthly with **animated underline**. Full-width rows, thin separators, left border accent for top row. Tabular numbers.

### Typography
- Tighter tracking, heavier weight where needed.
- Labels: uppercase, small, muted (`text-white/50`, `tracking-wider`).
- Numbers: `tabular-nums` for alignment.

### Components touched (V2 only)
- **GlassCard:** V1-style glass (`bg-[rgba(18,18,23,0.6)] backdrop-blur-md border border-white/10`), `rounded-md`, hover sweep and border accent.
- **OddsChip:** Rectangular, 1px border, V1 accent (#00FF5E), no pill.
- **ConfidenceMeter:** Rectangular bar, rounded ends, fill animation; pulse only at ≥80%.
- **SportBadge:** Rectangular, `rounded`, `border border-white/10 bg-white/5`.
- **PickCard:** Left accent, #00FF5E for AI badge, no bubbles.
- **Sidebar / TopBar / MobileNav:** Glass and #0A0F0A/#00FF5E; active state = left or top bar (#00FF5E), no pill tabs.
- **Leaderboard:** Segmented text + underline; table with lane hover sweep; rank badge rectangular; no avatars.

---

## Phase 3 — “Cool Stuff” Animations (V2 Only)

- **Page enter:** `AnimatedPage` wrapper (fade + slight y, 120–180ms) on dashboard, leaderboard, builder, analytics, settings.
- **Hover:** `v2-hover-sweep`, `v2-hover-lift`, border brighten.
- **Leaderboard row:** Lane sweep on hover.
- **Tab indicator:** Animated underline (e.g. leaderboard).
- **Confidence meter:** Fill from 0 → value on mount; smooth value changes; pulse at ≥80%.
- **Count-up:** `useCountUp` + `CountUpStat` for dashboard stats and leaderboard AI/Community cards (500–800ms).
- **Generate button:** Idle shine (`v2-shine-effect`), press scale (`v2-press-scale`).
- **Ambient:** Grid + scanline in V2 layout (existing), low opacity.
- **Reduced motion:** Respected in `animations.css` and `motion.ts`.

---

## Files Changed / Added (V2 Only)

### New
- `frontend/lib/v2/theme.ts`
- `frontend/styles/v2.css`
- `frontend/components/v2/CountUpStat.tsx`

### Modified
- `frontend/app/v2/layout.tsx` — import v2.css
- `frontend/app/v2/page.tsx` — bg #0A0F0A
- `frontend/app/v2/app/layout.tsx` — bg #0A0F0A
- `frontend/app/v2/app/page.tsx` — V1 colors, count-up, sharp CTAs
- `frontend/app/v2/app/leaderboard/page.tsx` — V1 colors, lane design, segmented tabs, CountUpStat
- `frontend/app/v2/app/builder/page.tsx` — AnimatedPage, V1 colors, sharp inputs/buttons
- `frontend/app/v2/app/analytics/page.tsx` — AnimatedPage, V1 colors, sharp cards
- `frontend/app/v2/app/settings/page.tsx` — AnimatedPage, V1 colors, sharp inputs/toggles
- `frontend/components/v2/GlassCard.tsx` — V1 glass + sharp
- `frontend/components/v2/OddsChip.tsx` — V1 accent, rectangular
- `frontend/components/v2/ConfidenceMeter.tsx` — V1 bar colors, rectangular
- `frontend/components/v2/SportBadge.tsx` — rectangular, border
- `frontend/components/v2/PickCard.tsx` — V1 colors, #00FF5E AI badge
- `frontend/components/v2/landing/V2HeroSection.tsx` — V1 hero (s1back.png, overlays, #00FF5E CTAs, sharp)
- `frontend/components/v2/landing/V2LivePicksSection.tsx` — V1 section styling
- `frontend/components/v2/landing/V2HowItWorksSection.tsx` — V1 glass cards, sharp
- `frontend/components/v2/landing/V2WhySection.tsx` — V1 glass cards, sharp
- `frontend/components/v2/landing/V2CtaSection.tsx` — V1 CTA + disclaimer
- `frontend/components/v2/app/V2DesktopSidebar.tsx` — V1 glass, #00FF5E active
- `frontend/components/v2/app/V2TopBar.tsx` — V1 bar + button
- `frontend/components/v2/app/V2MobileNav.tsx` — V1 glass, #00FF5E active, 44px tap

---

## Production / V1 Safety

- **No V1 or production files were changed.** No edits to `/`, `/app`, or any shared layouts, components, or global styles outside V2.
- All work is under:
  - `frontend/app/v2/**`
  - `frontend/components/v2/**`
  - `frontend/lib/v2/**`
  - `frontend/styles/v2.css` (imported only by `app/v2/layout.tsx`)
- Deleting the above V2 folders and `frontend/styles/v2.css` removes all changes.

---

## How to Preview

```bash
cd frontend
npm run dev
```

- **Landing:** [http://localhost:3000/v2](http://localhost:3000/v2)  
- **App (e.g. leaderboard):** [http://localhost:3000/v2/app/leaderboard](http://localhost:3000/v2/app/leaderboard)

Check: V1-style green (#00FF5E), glass panels, sharp corners, no bubbles/pills, leaderboard with segmented tabs and lane rows, count-up stats, and subtle animations.

---

## Acceptance Criteria (Met)

- Keeps V1 brand colors, transparency, and visual vibe.
- Looks more modern, edgy, and “high stakes.”
- No bubble/pill/circle UI patterns.
- More responsive (mobile bottom nav, 44px+ tap targets, no horizontal scroll).
- Interactions feel premium (animations subtle but present).
- Still isolated to V2; production unaffected.
