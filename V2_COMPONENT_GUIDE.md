# PARLAY GORILLA V2 - VISUAL COMPONENT GUIDE

## 🎨 COMPONENT SHOWCASE

### 1. ODDS CHIP (`OddsChip.tsx`)
**Purpose**: Display betting odds in sportsbook style

**Variants**:
- `default` - Neutral gray background
- `positive` - Green for underdog/positive odds
- `negative` - Red for favorite/negative odds

**Sizes**:
- `sm` - Compact (text-xs, px-2)
- `md` - Standard (text-sm, px-3)
- `lg` - Large (text-base, px-4)

**Usage**:
```tsx
<OddsChip odds={-110} size="md" variant="default" />
<OddsChip odds={150} size="sm" variant="positive" />
```

**Visual**: Rounded chips with border, displays formatted odds (+150, -110)

---

### 2. CONFIDENCE METER (`ConfidenceMeter.tsx`)
**Purpose**: Visual confidence percentage indicator

**Features**:
- Color-coded by threshold:
  - 75%+ → Emerald (high confidence)
  - 65-74% → Yellow (medium confidence)
  - <65% → Orange (lower confidence)
- Animated progress bar
- Optional label display

**Sizes**: `sm`, `md`, `lg`

**Usage**:
```tsx
<ConfidenceMeter confidence={78} showLabel={true} size="md" />
```

**Visual**: Horizontal progress bar with percentage label

---

### 3. SPORT BADGE (`SportBadge.tsx`)
**Purpose**: Color-coded sport/league indicators

**Sport Colors**:
- NFL → Blue (`bg-blue-500/20 text-blue-300`)
- NBA → Orange (`bg-orange-500/20 text-orange-300`)
- NHL → Cyan (`bg-cyan-500/20 text-cyan-300`)
- MLB → Red (`bg-red-500/20 text-red-300`)
- NCAAF → Purple
- NCAAB → Amber

**Usage**:
```tsx
<SportBadge sport="nfl" league="NFL" size="md" />
```

**Visual**: Rounded badge with uppercase league text

---

### 4. GLASS CARD (`GlassCard.tsx`)
**Purpose**: Glass morphism card container

**Features**:
- Backdrop blur effect
- Semi-transparent background
- Optional hover state
- Configurable padding

**Padding Options**: `none`, `sm`, `md`, `lg`

**Usage**:
```tsx
<GlassCard padding="lg" hover={true}>
  {children}
</GlassCard>
```

**Visual**: Elevated card with frosted glass effect

---

### 5. PICK CARD (`PickCard.tsx`)
**Purpose**: Display a single pick with all relevant info

**Variants**:
- `compact` - For carousels/lists (280px min-width)
- `full` - Detailed view with all metadata

**Data Displayed**:
- Sport badge
- AI pick indicator
- Matchup
- Pick details
- Odds chip
- Confidence meter
- Game time

**Usage**:
```tsx
<PickCard pick={mockPick} variant="compact" onSelect={() => {}} />
<PickCard pick={mockPick} variant="full" />
```

**Visual**: Card with organized pick information, hover effect

---

## 📱 NAVIGATION COMPONENTS

### 6. DESKTOP SIDEBAR (`V2DesktopSidebar.tsx`)
**Visibility**: ≥1024px (lg breakpoint)

**Sections**:
1. **Logo Area** (top)
   - Gorilla emoji logo
   - "Parlay Gorilla" text
   - "V2 PREVIEW" badge

2. **Navigation** (middle)
   - Dashboard 🏠
   - Builder 🎯
   - Analytics 📊
   - Leaderboard 🏆
   - Settings ⚙️

3. **Account Section** (bottom)
   - User avatar
   - Username
   - Plan badge

**Features**:
- Active route highlighting (emerald background)
- Smooth hover transitions
- Sticky positioning

---

### 7. MOBILE BOTTOM NAV (`V2MobileNav.tsx`)
**Visibility**: <1024px

**Tabs** (4 primary actions):
- Builder 🎯
- Picks 🏠
- Stats 📊
- Settings ⚙️

**Features**:
- Fixed to bottom of screen
- Grid layout (4 columns)
- Active tab highlighting
- 44px+ tap targets
- Icon + label format

---

### 8. TOP BAR (`V2TopBar.tsx`)
**Visibility**: All screen sizes

**Layout**:
- **Mobile**: Logo (left) + Generate button (right)
- **Desktop**: Page title (left) + Generate button (right)

**Features**:
- Sticky positioning
- Backdrop blur
- Emerald green CTA button

---

## 🏠 LANDING PAGE SECTIONS

### 9. HERO SECTION (`V2HeroSection.tsx`)
**Height**: 85vh

**Elements**:
- Trust indicators (AI-Driven, Data-Backed, Built for Degens)
- Main headline: "Stop Guessing. Build Smarter Parlays."
- Subheadline
- Primary CTA: "Build a Parlay" (emerald)
- Secondary CTA: "View Today's Picks" (slate)
- Disclaimer text

**Background**:
- Dark gradient (slate-900 → slate-950)
- Grid pattern overlay (emerald, 3% opacity)

---

### 10. LIVE PICKS SECTION (`V2LivePicksSection.tsx`)
**Features**:
- Horizontal scrolling container
- Compact pick cards
- "Scroll for more" hint
- Snap scrolling

**Layout**: Flex row with overflow-x-auto

---

### 11. HOW IT WORKS (`V2HowItWorksSection.tsx`)
**Steps** (3 cards):
1. Choose Your Sport 🏈
2. AI Analyzes Data 🤖
3. Build Your Parlay 📊

**Visual**: Grid layout, numbered steps, background gradient

---

### 12. WHY SECTION (`V2WhySection.tsx`)
**Features** (4 items):
- AI Confidence Engine 🎯
- Correlation Awareness 🔗
- Multi-Sport Support 🏆
- No Gut Picks 📈

**Layout**: 2-column grid (responsive)

---

### 13. CTA SECTION (`V2CtaSection.tsx`)
**Elements**:
- Final headline
- "Get Started Now" CTA
- Full disclaimer (bordered section)

---

## 📄 APP PAGES

### 14. DASHBOARD (`/v2/app`)
**Sections**:
1. Stats cards (4-column grid)
   - Win Rate
   - Total Picks
   - Avg Confidence
   - ROI
2. Today's AI picks (2-column grid)
3. Quick actions

---

### 15. BUILDER (`/v2/app/builder`)
**Layout**: 2/3 + 1/3 grid

**Left Side** (2/3):
- Available picks list
- Click to select (ring highlight)

**Right Side** (1/3):
- Parlay slip (sticky)
- Selected picks list
- Stats (legs, odds, confidence)
- Stake input
- Potential payout
- "Build Parlay" CTA

---

### 16. ANALYTICS (`/v2/app/analytics`)
**Sections**:
1. Summary cards (4-column)
2. Win rate by sport (chart)
3. Confidence vs outcome (breakdown)
4. Recent bets (list)

---

### 17. LEADERBOARD (`/v2/app/leaderboard`)
**Features**:
- Daily/weekly/monthly tabs
- Table with rankings
- AI vs community comparison cards

**Columns**:
- Rank (medals for top 3)
- User (avatar + name)
- Win Rate
- Total Picks
- ROI
- Avg Confidence

---

### 18. SETTINGS (`/v2/app/settings`)
**Sections**:
1. Account (username, email)
2. Notifications (toggles)
3. Display (dark mode, odds format)
4. Subscription (plan badge, upgrade CTA)
5. Danger zone (reset/delete)

---

## 🎨 COLOR SYSTEM

**Backgrounds**:
- Primary: `bg-slate-950` (#0a0a0f)
- Secondary: `bg-slate-900` (#0f172a)
- Cards: `bg-slate-800/40` (semi-transparent)

**Accents**:
- Primary CTA: `bg-emerald-500` (#22c55e)
- Hover: `bg-emerald-400`
- Text: `text-emerald-400`

**Text**:
- Primary: `text-white`
- Secondary: `text-slate-400`
- Muted: `text-slate-500`
- Disabled: `text-slate-600`

**Status Colors**:
- Success/Win: `emerald-400`
- Warning: `yellow-400`
- Error/Loss: `red-400`
- Info: `cyan-400`

---

## 🔧 UTILITY CLASSES

**Rounded Corners**:
- Small: `rounded-md` (6px)
- Medium: `rounded-lg` (8px)
- Large: `rounded-xl` (12px)
- Full: `rounded-full` (circle)

**Transitions**:
- Default: `transition-all duration-200`
- Colors: `transition-colors duration-200`

**Shadows**:
- CTA: `shadow-lg shadow-emerald-500/25`
- Hover: `shadow-emerald-500/40`

---

## 📐 RESPONSIVE BREAKPOINTS

- Mobile: `< 1024px`
  - Bottom navigation
  - Single column layouts
  - Stacked cards

- Desktop: `≥ 1024px`
  - Sidebar navigation
  - Multi-column grids
  - Wider content areas

**Tailwind Breakpoint**: `lg:` prefix for desktop styles

---

## 🧪 MOCK DATA STRUCTURE

**MockPick**:
```typescript
{
  id: string
  sport: Sport
  league: string
  matchup: string
  homeTeam: string
  awayTeam: string
  pick: string
  pickType: 'moneyline' | 'spread' | 'total'
  odds: number
  confidence: number
  gameTime: string
  aiGenerated: boolean
}
```

**MockLeaderboardEntry**:
```typescript
{
  rank: number
  username: string
  winRate: number
  totalPicks: number
  roi: number
  avgConfidence: number
}
```

---

**ALL COMPONENTS ARE PRODUCTION-READY AND FULLY FUNCTIONAL WITH MOCK DATA.**
