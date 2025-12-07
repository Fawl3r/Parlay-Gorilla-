# 🦍 Parlay Gorilla – Master System Prompt (Web-Only, 1–20 Leg Parlays)

You are building **Parlay Gorilla**, a full-stack **web app** (NOT a mobile app) that creates **high-confidence 1–20 leg parlays** using a multi-sport predictive AI engine.

The goal:
- Generate **legit, data-backed parlays** (not random 50/50 junk).
- Show **clear model probabilities** and **EV-based reasoning**.
- Be **SEO-optimized** to win **Google featured snippets** for matchup prediction searches.
- Include a **premium paywall** (LemonSqueezy + Coinbase Commerce).
- Include a **full admin dashboard** with detailed analytics.

The UX must be **visually fire**: neon cyber-gorilla / sports betting / futuristic AI vibes, with animations and strong visual hierarchy.

---

## 0. Tech Stack (Locked)

**Backend**
- Language: Python
- Framework: FastAPI
- DB: PostgreSQL
  - Dev: Local Postgres via Docker
  - Prod: Neon or Railway Postgres
- ORM: SQLAlchemy + Alembic migrations
- Background jobs: simple worker / scheduler (e.g. APScheduler or custom FastAPI background tasks)
- External APIs:
  - Odds API (primary odds)
  - SportsRadar (schedules, stats, injuries) – integrate via HTTP client
  - ESPN scraper (HTML scraping for matchup context, power rankings, etc.)
- AI: OpenAI API for narrative game analysis + parlay explanation

**Frontend**
- Framework: Next.js (App Router) + TypeScript
- Styling: Tailwind CSS (and optional shadcn UI components)
- Charts: Any simple TS-friendly chart lib (e.g. Recharts) for admin and confidence visualizations

**Infra**
- Folder layout:
  - `/backend/app/...`
  - `/frontend/app/...`
  - `/infra/...` for Docker, configs
- DB migrations via Alembic CLI
- No Supabase/Firebase. DB must be accessible via CLI (`psql`, Alembic, etc.).

---

## 1. Core User-Facing Screens (Web Only)

Implement these as **Next.js App Router pages** with clean, animated UI:

1. **Welcome Screen (Landing Page)**
   - Hero: Massive **cyber gorilla** + neon sports arena background.
   - CTA buttons:
     - "Generate a Parlay"
     - "View Today's Game Analysis"
   - Quick explanation of:
     - "What is Parlay Gorilla?"
     - "How the AI works" (data sources + confidence system)
   - Sections:
     - Why Parlay Gorilla? (3–6 icon cards)
     - How It Works (3 steps with icons)
     - Screenshot-style previews of Game Grid + AI Parlay Builder
   - Ad slots (placeholders) for future banner ads (top, mid-page, footer).

2. **Sports Selection Screen**
   - Path: `/sports`
   - Show major sports:
     - NFL, NBA, NHL, MLB, Soccer (EPL/MLS at minimum)
   - Each sport: large tile card with icon, short description, and "View Games".
   - Filtering for:
     - Today / Upcoming / By Date
   - Click → goes to Game Grid for that sport and date.

3. **Game Grid Screen**
   - Path example: `/games/nfl/today`
   - Table/grid of matchups:
     - Away vs Home
     - Moneyline odds
     - Spread
     - Total
     - Model Win Probability (home/away)
     - "View Analysis" button → `/analysis/{sport}/{away}-vs-{home}-prediction`
     - "Add to Parlay" button (to feed into the AI Parlay Builder / bet slip).
   - Indicator for **"Gorilla Upset Candidate"** when model sees strong +EV on underdogs.

4. **AI Parlay Builder Screen**
   - Path: `/parlays/ai-builder`
   - This is the **core Parlay Gorilla AI** flow.
   - Controls:
     - Sport filters (multi-select)
     - Parlay type:
       - Safe / Balanced / Degen
     - Number of legs: **1–20** (slider or stepper)
     - Toggle: "Include Gorilla Upsets" (on by default for Balanced/Degen)
   - On "Generate Parlay":
     - Calls backend `/api/parlay/build` endpoint.
     - Shows:
       - List of legs (sport, matchup, market type, odds, model probability).
       - Tag for **"Upset"** legs (plus risk tier).
       - Combined parlay odds.
       - Model combined win probability.
       - EV estimate.
       - Short AI explanation ("why these legs?").

   - **Free vs Premium Logic:**
     - Free users:
       - Can use this **AI Parlay Builder** to generate **ONE parlay (configurable, default: 1 per day)**.
       - After limit reached → show **Premium Paywall**.
     - Paid users:
       - Unlimited AI parlay generations (within rate limits).
       - Extra filters (e.g. EV threshold, multi-sport mixing).

5. **Odds Heatmap Screen**
   - Path: `/tools/odds-heatmap`
   - Visual display:
     - Games down the Y-axis, bookmakers or markets on X-axis (or simplified version).
     - Colors reflect **value edge**: model probability vs implied probability.
     - Highlight:
       - Legs with biggest **positive edge**.
       - Upset candidates.
   - Option to "Add to Parlay" from heatmap.

6. **Confidence Score Meter**
   - Component reused across screens, not just one page.
   - Visual:
     - Circular or bar gauge showing **model confidence** for:
       - Single leg
       - Whole parlay
   - Use:
     - In game analysis pages:
       - "Model Confidence: 67% win chance for Team X"
     - In parlay results:
       - "Parlay Confidence: 74% (based on combined model probabilities)".

7. **1–20 Leg Parlay Generator Screen**
   - Path: `/parlays/generator`
   - This page is similar to AI Builder but focused on **bulk generation**:
     - Input:
       - min_legs, max_legs (1–20)
       - parlay type (safe/balanced/degen)
     - Output:
       - Show multiple parlay options:
         - "Safe Ticket"
         - "Balanced Ticket"
         - "Degen Ticket"
       - Each with EV, combined odds, model confidence.
   - Paid-only feature or heavily limited for free users.

8. **Parlay Result Probability Screen**
   - Path: `/parlays/result/[id]`
   - When a parlay is built (AI or user custom), show:
     - Each leg with:
       - model probability,
       - implied probability,
       - value edge,
       - upset tag
     - Combined:
       - Probability of hit
       - EV
       - Individual leg sensitivity (which leg is most likely to bust the ticket).
   - Visualizations:
     - Confidence gauge
     - "Bust risk breakdown" chart.

9. **Bet Slip Animation**
   - Component for any parlay confirmation screen.
   - Animated "bet slip" that:
     - Slides in from right/bottom.
     - Shows parlay legs.
     - Glowing neon gorilla stamp animation on "AI Approved" tickets.
   - No real money betting, just prediction & visualization.

10. **Parlay History Screen**
    - Path: `/parlays/history`
    - Requires login.
    - Shows:
      - List of parlays generated by the user (AI + custom).
      - Filters by:
        - Date
        - Sport
        - Result: still pending / hit / missed.
      - For completed games:
        - Show **hit/miss** per leg.
        - Show whether the parlay hit.
    - Data source:
      - Use model prediction tracking and game result resolution from the backend.

11. **Premium Paywall Screen**
    - Path: `/premium`
    - Fully **explains premium membership**:
      - Unlimited AI parlays (vs 1 free).
      - Access to custom parlay builder.
      - Access to multi-sport parlays.
      - Access to "Gorilla Upset Finder".
      - Early access to new sports/tools.
      - No or fewer ads.
    - Integrations:
      - **LemonSqueezy** for card-based subscriptions.
      - **Coinbase Commerce** for crypto payments.
    - Show clearly:
      - Monthly / yearly plans.
      - What free users get vs premium.
    - Strong, persuasive copy, benefit focused (not just feature list).

> NOTE: **Game analysis pages must remain free / public** (no paywall).

---

## 2. Game Analysis Pages + SEO (Featured Snippets)

**Goal:** When someone Googles "Team A vs Team B prediction", our analysis page should be favored for **featured snippets**.

### 2.1 URL Pattern
- Use:
  - `/analysis/{sport}/{away-team}-vs-{home-team}-prediction`
  - Example: `/analysis/nfl/bears-vs-packers-prediction`

### 2.2 Page Layout
Immediately after `<h1>`, show a concise **answer block**:

- H1: `{Matchup} Prediction & Betting Picks`
- Answer block (component): `SnippetAnswerBlock`
  - "Who will win {matchup}?"
  - "Our model gives the {Team X} a {YY}% chance to win. Best bet: {pick} because {1–2 line rationale}."

Below that:
- Sections:
  - Offensive Matchup Analysis
  - Defensive Matchup Analysis
  - ATS Trends & Betting History
  - Best Bets for {matchup}
- Internal links to:
  - Other games in same sport
  - Team pages if they exist

### 2.3 Structured Data (JSON-LD)
Implement helpers in `frontend/lib/seo/schema.ts`:

- `buildSportsEventSchema(analysis: GameAnalysis)`
  - Uses type `SportsEvent` with homeTeam, awayTeam, startDate, venue, offers (odds).
- `buildFAQPageSchema(analysis: GameAnalysis)`
  - Uses type `FAQPage` with 3 QA:
    - Who will win?
    - What is the spread?
    - What is the best bet?

Inject via `<script type="application/ld+json">`.

### 2.4 Sitemap
- Implement `frontend/app/sitemap.ts`:
  - Auto lists all analysis pages with `lastmod`.
  - Ensures search engines discover new matchups quickly.

---

## 3. Prediction Engine, Upsets, and Learning Loop

Implement the **backend engine** as per the earlier plan:

### 3.1 Feature Pipeline
File: `backend/app/services/feature_pipeline.py`

Build a **MatchupFeatureVector** per game using:

- SportsRadar: offense, defense, pace, recent form, rest days, etc.
- Odds API: odds + implied probabilities.
- ESPN scraper: matchup context, power rankings, H2H.
- Weather API for outdoor games.
- Injury severity scores (SportsRadar + ESPN notes).
- Home/away factors and travel distances.

### 3.2 Per-Sport Engines
File: `backend/app/services/probability_engine.py`

Engines:
- NFLProbabilityEngine
- NBAProbabilityEngine
- NHLProbabilityEngine
- MLBProbabilityEngine
- SoccerProbabilityEngine

Each:
- Accepts MatchupFeatureVector.
- Outputs:
  - home_win_prob
  - away_win_prob
  - spread_cover_prob
  - projected_total_points/goals
- Apply **team bias calibration** corrections from learning loop.

### 3.3 Prediction Tracking & Calibration
Models:
- `ModelPrediction`
- `PredictionOutcome`
- `TeamCalibration`

Service: `PredictionTrackerService`

Flow:
1. When an analysis is generated:
   - Save the model prediction (with snapshot of features, implied vs model prob).
2. After games complete:
   - Background job resolves predictions:
     - Correct vs incorrect.
     - Error magnitude.
   - Update team bias data.
3. Engines:
   - Apply small bias adjustments per team (clamped) and re-normalize.

Goal:
- Over time, **Parlay Gorilla learns where it overrates/underrates teams** and adjusts probabilities.

---

## 4. Parlay Builder & Gorilla Upset Logic

File: `backend/app/services/parlay_builder.py`

- **find_upset_candidates(games, threshold)**:
  - Finds +money sides where model_prob – implied_prob ≥ threshold.
  - Tags each with `risk_tier` (low/medium/high).
- **build_parlay(...)**:
  - Accepts:
    - sport_filters
    - parlay_type (safe, balanced, degen)
    - max_legs (1–20)
    - optional target EV
  - Uses:
    - favorites (negative odds)
    - upsets (from `find_upset_candidates`)
  - Applies **UPSET_CAPS**:
    - Safe: very few low-risk upsets
    - Balanced: moderate number of medium/low upsets
    - Degen: more upsets, up to defined cap
  - Returns:
    - legs with odds, model_prob, upset_tag
    - combined EV and model confidence

Endpoints in `backend/app/api/routes/parlay.py`:
- `GET /api/parlay/upsets/{sport}`
- `POST /api/parlay/build`

---

## 5. Admin Dashboard & Analytics

Create a **protected admin system** (web-only, no mobile):

### 5.1 Admin Auth
- Simple admin role:
  - Add `User` model with `role` (user/admin).
  - Restrict `/admin` routes and pages to `role == "admin"`.

### 5.2 Metrics to Track
Backend DB tables / logic to aggregate:

- **User metrics**
  - Total registered users
  - Daily/weekly active users
  - Free vs premium counts
  - Conversion rate from free → premium

- **Usage metrics**
  - Number of AI parlays generated (per day, sport, parlay type)
  - Number of manual (user-built) parlays
  - Average legs per parlay
  - Most popular sports and markets
  - Usage of Gorilla Upset Finder

- **Prediction performance**
  - Model accuracy by sport and market (moneyline/spread/total)
  - Brier score, calibration charts
  - Upset hit rate vs market

- **SEO & traffic**
  - Pageview counts per analysis page (store internally, not Google Analytics)
  - Top pages by traffic
  - Traffic by sport and team
  - Basic referrer tracking (if easy to include)

- **Revenue**
  - Subscriptions events from LemonSqueezy
  - Crypto payments from Coinbase Commerce
  - MRR, total revenue, ARPU summaries

### 5.3 Admin UI
Path: `/admin`

Sections:
- Dashboard Overview:
  - Cards: Total users, Active users, Premium users, MRR, Today's AI parlays.
  - Simple line chart: daily active users.
  - Simple line chart: AI parlays per day.

- Usage:
  - Table: per sport usage (parlays, analysis views).
  - Chart: breakdown of parlay types (safe/balanced/degen).

- Model Performance:
  - Chart: accuracy over time.
  - Table: accuracy by sport + market.
  - "Top over-/underperforming teams" (based on bias metrics).

- Revenue:
  - Table of subscription plans and counts.
  - Graph of revenue over time.

- System:
  - Toggle for enabling/disabling certain sports.
  - Configurable free user limits:
    - Max AI parlays per day.
  - Ad toggles: show/hide ad slots across site (for later AdSense integration).

---

## 6. Subscription & Paywall Logic (LemonSqueezy + Coinbase Commerce)

### 6.1 Free vs Premium Rules

- **Free Users**
  - Can:
    - View **all game analysis pages** (no restriction).
    - Generate **1 AI parlay** (via Parlay Gorilla AI Builder) per day (make this a configurable value).
    - View odds heatmap in a limited manner if desired (e.g. only top few rows).
  - Cannot:
    - Use **Custom Parlay Builder** (user-built full control).
    - Use bulk 1–20 leg generator.
    - Access Gorilla Upset Finder detail views (only hints/teasers).
    - Access Parlay History beyond a small recent limit (configurable).

- **Premium Users**
  - Unlock:
    - Unlimited AI parlays (within rate limits).
    - Full custom parlay builder.
    - Full Gorilla Upset Finder.
    - Full parlay history.
    - Additional filters/controls (EV filters, sport mixes).
    - Reduced/no ads.

### 6.2 Integration

Implement integration modules:
- `backend/app/services/payments/lemonsqueezy.py`
  - Webhook handler to mark user as premium / downgrade on cancel.
- `backend/app/services/payments/coinbase_commerce.py`
  - Webhook handler to mark user as premium after confirmed payment.

Frontend:
- Premium Paywall page clearly shows all feature differences.
- In gated features:
  - Detect user plan → if free and over limit or in premium-only feature:
    - Show modal / overlay:
      - Quick summary: "What you get with Premium"
      - Direct link to `/premium` page.

---

## 7. Ads & Monetization (Non-Intrusive)

- Add reusable `AdSlot` component that:
  - Accepts `slotId` and `position`.
  - Currently placeholder only (no actual ad code now).
- Place in:
  - Landing page
  - Game analysis pages (below fold)
  - Possibly tools pages

Make sure:
- Ads never block core UX.
- Premium users can have ads hidden (configurable).

---

## 8. Implementation Rules for Cursor

1. **Always keep it real**: Use real data from Odds API, SportsRadar, ESPN. No mock placeholders once wiring passes are done.
2. **Type-safety**:
   - Use TypeScript with strict types for frontend.
   - Use Pydantic models / schemas for request/response in FastAPI.
3. **Separation of concerns**:
   - Data fetchers in `/backend/app/services/data_fetchers/...`
   - Prediction logic in `probability_engine.py`
   - Parlay logic in `parlay_builder.py`
   - SEO helpers in `frontend/lib/seo/schema.ts`
   - Reusable UI components in `frontend/components/...`
4. **Testing**:
   - Add unit tests for:
     - Feature pipeline
     - Probability engines
     - Parlay builder (EV, upset caps, etc.)
     - Prediction tracking
     - SEO schema validity
5. **No mobile implementation**:
   - Only build **responsive web UI**.
   - Do NOT implement native mobile apps or Expo code.

---

## 9. What to Work On First

When starting or resuming work, prioritize in this order:

1. Core data pipeline + per-sport probability engines (NFL, NBA, NHL, MLB, Soccer).
2. Parlay builder + Gorilla Upset logic.
3. Game analysis pages with snippet-optimized answer block + JSON-LD.
4. AI narrative integration (OpenAI) for analysis/explanations.
5. Premium paywall logic (free vs premium) + LemonSqueezy / Coinbase Commerce.
6. Admin dashboard with analytics.
7. UI polish: animations, gorilla branding, odds heatmap, confidence meters.
8. Tests + cleanup.

Always follow the rules above and keep the codebase production-ready and extensible.

