# Parlay Gorilla – 20-Leg Predictive Parlay Engine

An AI-powered sports betting assistant that generates 1–20 leg parlays with win probabilities, confidence scores, and detailed explanations.

Key capabilities:
- **AI Builder**: generate Safe/Balanced/Degen parlays.
- **Custom Builder**: build your own ticket and get probability/edge analysis, plus a **Counter / Upset Ticket** generator that flips your picks on the same games where the model sees the best edge.

## Project Structure

This is a monorepo containing:

- `backend/` - FastAPI application for odds fetching, predictions, and parlay generation
- `frontend/` - Next.js application for the user interface

## Tech Stack

### Backend
- **Framework:** FastAPI
- **Database:** Render PostgreSQL
- **ORM:** SQLAlchemy (async)
- **External APIs:** The Odds API, OpenAI, SportsRadar, ESPN
- **Authentication:** JWT-based with bcrypt password hashing
- **Payment Processing:** LemonSqueezy, Coinbase Commerce
- **Blockchain:** Solana (IQ Labs) for proof anchoring

### Frontend
- **Framework:** Next.js 14+ (App Router)
- **Styling:** Tailwind CSS
- **Components:** shadcn/ui
- **Language:** TypeScript

## System Architecture

Parlay Gorilla is a monorepo with three main runtime services:

```
┌─────────────────┐
│   Frontend      │  Next.js (www.parlaygorilla.com)
│   (Next.js)     │  └─> API calls via /api/* rewrites
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Backend API   │  FastAPI (api.parlaygorilla.com)
│   (FastAPI)     │  └─> JWT auth, parlay generation, webhooks
└────────┬────────┘
         │
    ┌────┴────┬──────────────┬─────────────┐
    ▼         ▼              ▼             ▼
┌────────┐ ┌──────┐  ┌──────────────┐  ┌──────────┐
│Postgres│ │Redis │  │External APIs │  │Blockchain│
│   DB   │ │Cache │  │(Odds, OpenAI)│  │ (Solana) │
└────────┘ └──────┘  └──────────────┘  └──────────┘
         │
         ▼
┌─────────────────┐
│Inscriptions     │  Node.js Worker (background)
│Worker           │  └─> Blockchain proof anchoring
└─────────────────┘
```

### Components

1. **Frontend (Next.js)**
   - Serves user interface at `www.parlaygorilla.com`
   - Proxies API calls to backend via Next.js rewrites
   - Handles authentication, parlay building, analytics
   - Deployed on Render

2. **Backend API (FastAPI)**
   - RESTful API at `api.parlaygorilla.com`
   - Handles authentication, parlay generation, payments
   - Processes webhooks from payment providers
   - Manages user subscriptions and credits
   - Deployed on Render

3. **Inscriptions Worker (Node.js)**
   - Background service for blockchain operations
   - Anchors custom parlay proofs on Solana
   - Uses IQ Labs SDK for inscriptions
   - Deployed on Render as worker service

4. **Database (PostgreSQL)**
   - Render managed PostgreSQL
   - Stores users, games, odds, parlays, subscriptions
   - Auto-wired via `render.yaml` Blueprint

5. **Cache (Redis)**
   - Render Key Value store
   - Distributed odds API cache
   - Scheduler coordination
   - Auto-wired via `render.yaml` Blueprint

## Data Flow

### User Registration & Authentication

```
1. User submits registration form
   ↓
2. Frontend → POST /api/auth/register
   ↓
3. Backend validates email/password
   ↓
4. Backend hashes password (bcrypt)
   ↓
5. Backend creates user in PostgreSQL
   ↓
6. Backend generates JWT token
   ↓
7. Backend sends verification email (Resend)
   ↓
8. Frontend stores JWT in localStorage
   ↓
9. User authenticated for subsequent requests
```

**Key Files:**
- `backend/app/api/routes/auth.py` - Auth endpoints
- `backend/app/services/auth_service.py` - Auth logic
- `backend/app/models/user.py` - User model
- `frontend/lib/api/services/AuthApi.ts` - Frontend auth client

### Parlay Generation Flow

```
1. User selects sport(s) and risk profile
   ↓
2. Frontend → POST /api/parlay/generate
   ↓
3. Backend checks user access (free/subscription/credits)
   ↓
4. Backend fetches games/odds (cached or from The Odds API)
   ↓
5. Backend generates parlay picks using AI
   ↓
6. Backend calculates win probabilities
   ↓
7. Backend generates explanations (OpenAI)
   ↓
8. Backend saves parlay to database
   ↓
9. Backend returns parlay with probabilities
   ↓
10. Frontend displays parlay to user
```

**Key Files:**
- `backend/app/api/routes/parlay.py` - Parlay endpoints
- `backend/app/services/parlay_builder.py` - Parlay generation
- `backend/app/core/access_control.py` - Access control logic

### Payment & Subscription Flow

```
1. User purchases subscription/credits
   ↓
2. Frontend redirects to LemonSqueezy/Coinbase checkout
   ↓
3. User completes payment
   ↓
4. Payment provider sends webhook → POST /api/webhooks/*
   ↓
5. Backend verifies webhook signature (HMAC-SHA256)
   ↓
6. Backend checks idempotency (prevents duplicate processing)
   ↓
7. Backend activates subscription/adds credits
   ↓
8. Backend logs payment event
   ↓
9. User's account updated in database
```

**Key Files:**
- `backend/app/api/routes/webhooks/lemonsqueezy_webhook_routes.py`
- `backend/app/api/routes/webhooks/coinbase_webhook_routes.py`
- `backend/app/models/payment_event.py` - Payment logging

### Affiliate Attribution Flow

```
1. User clicks affiliate link (with cookie)
   ↓
2. Frontend stores affiliate cookie
   ↓
3. User registers/logs in
   ↓
4. Backend reads affiliate cookie
   ↓
5. Backend attributes user to affiliate
   ↓
6. Backend creates referral record
   ↓
7. Future purchases generate commissions
   ↓
8. Commissions tracked in database
```

**Key Files:**
- `backend/app/services/affiliate_cookie_attribution_service.py`
- `backend/app/models/affiliate_referral.py`

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- The Odds API key (free tier available)
- OpenAI API key

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy environment variables:
```bash
cp .env.example .env
```

5. Update `.env` with your credentials:
   - `DATABASE_URL`: Your PostgreSQL connection string (Render PostgreSQL in production, local Postgres in dev)
   - `USE_SQLITE=false`: Disable SQLite fallback
   - `REDIS_URL`: Redis URL (required in production)
   - `THE_ODDS_API_KEY`: Your The Odds API key
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `JWT_SECRET`: JWT signing secret (required in production)
   - `RESEND_API_KEY` (optional): enables verification + password reset emails

6. Run the development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Copy environment variables:
```bash
cp .env.example .env.local
```

4. Update `.env.local` with your backend URL:
   - `NEXT_PUBLIC_API_URL`: Backend API URL (default: `http://localhost:8000`)

5. Run the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Database Setup

### Render PostgreSQL (Recommended)

For production, use **Render PostgreSQL** and deploy with the repo’s root `render.yaml` Blueprint.

- The Blueprint wires `DATABASE_URL` automatically from Render Postgres.
- The backend converts `postgresql://` → `postgresql+asyncpg://` automatically for async SQLAlchemy.

### Database Schema

The application uses three main tables:

- **games** - Stores game/match information
- **markets** - Stores betting markets (moneyline, spread, totals) per game
- **odds** - Stores specific odds for each market outcome

All tables include proper indexes for efficient querying.

## Key File Locations

### Backend

**Authentication:**
- `backend/app/api/routes/auth.py` - Authentication endpoints (login, register, password reset)
- `backend/app/services/auth_service.py` - Authentication logic (password hashing, JWT generation)
- `backend/app/models/user.py` - User database model
- `backend/app/core/dependencies.py` - Database session and current user dependencies

**Parlay Generation:**
- `backend/app/api/routes/parlay.py` - Parlay generation endpoints
- `backend/app/services/parlay_builder.py` - Parlay building logic
- `backend/app/core/access_control.py` - Access control (free/subscription/credits)

**Webhooks:**
- `backend/app/api/routes/webhooks/lemonsqueezy_webhook_routes.py` - LemonSqueezy webhook handler
- `backend/app/api/routes/webhooks/coinbase_webhook_routes.py` - Coinbase Commerce webhook handler

**Database:**
- `backend/app/models/` - All database models (User, Parlay, Payment, Subscription, etc.)
- `backend/app/database/session.py` - Database connection and session management
- `backend/alembic/versions/` - Database migration files

**Configuration:**
- `backend/app/core/config.py` - Application settings and environment variables
- `render.yaml` - Render deployment configuration (auto-wires services)

### Frontend

**API Client:**
- `frontend/lib/api/` - API client library
  - `frontend/lib/api/services/AuthApi.ts` - Authentication API
  - `frontend/lib/api/services/ParlayApi.ts` - Parlay API
  - `frontend/lib/api/services/SubscriptionApi.ts` - Subscription API

**Pages:**
- `frontend/app/` - Next.js App Router pages
- `frontend/components/` - React components

**Configuration:**
- `frontend/next.config.js` - Next.js configuration (API rewrites)

## API Endpoints

### Authentication (`/api/auth/*`)
- `POST /api/auth/register` - Register new user (rate limited: 5/min)
- `POST /api/auth/login` - Login user (rate limited: 10/min)
- `POST /api/auth/forgot-password` - Request password reset (rate limited: 5/hour)
- `POST /api/auth/reset-password` - Reset password with token (rate limited: 10/hour)
- `GET /api/auth/me` - Get current user profile
- `POST /api/auth/verify-email` - Verify email address

### Parlay Generation (`/api/parlay/*`)
- `POST /api/parlay/generate` - Generate AI parlay (rate limited: 20/hour)
- `POST /api/parlay/triple` - Generate triple parlay (rate limited: 20/hour)
- `GET /api/parlay/history` - Get user's parlay history
- `GET /api/parlay/{id}` - Get specific parlay details

### Custom Parlay Builder (`/api/custom-parlay/*`)
- `POST /api/custom-parlay/analyze` - Analyze custom parlay (rate limited: 30/hour)
- `POST /api/custom-parlay/upset-finder` - Generate counter ticket (rate limited: 20/hour)
- `POST /api/custom-parlay/save` - Save custom parlay

### Games & Analysis (`/api/games/*`, `/api/analysis/*`)
- `GET /api/sports/{sport}/games` - Get games for sport
- `GET /api/analysis/{sport}/{slug}` - Get game analysis
- `GET /api/analysis/list` - List available analyses

### Webhooks (`/api/webhooks/*`)
- `POST /api/webhooks/lemonsqueezy` - LemonSqueezy webhook (signature verified)
- `POST /api/webhooks/coinbase` - Coinbase Commerce webhook (signature verified)

### Subscription & Billing (`/api/subscription/*`, `/api/billing/*`)
- `GET /api/subscription/me` - Get user subscription status
- `GET /api/billing/history` - Get payment history
- `GET /api/billing/plans` - Get available subscription plans

### Admin (`/api/admin/*`)
- Requires admin role authentication
- User management, metrics, payments, affiliates, tax reporting

### Health & Metrics
- `GET /health` - API health check
- `GET /api/metrics` - Application metrics

**Note:** All authenticated endpoints require JWT token in `Authorization: Bearer <token>` header.

## Development

### Quick Start - Run Both Servers

The easiest way to run both backend and frontend together:

**Windows:**
```bash
# Command Prompt
run-dev.bat

# PowerShell
.\run-dev.ps1
```

**Mac/Linux:**
```bash
./run-dev.sh
```

These scripts will:
- Check for required dependencies (Python, Node.js)
- Install frontend dependencies if needed
- Check if ports 8000 and 3000 are available
- Start both servers in separate windows/processes
- Display local and network access URLs

**Note:** The servers will continue running after the script exits. Close the server windows or press Ctrl+C in them to stop.

### Backend Development

- Main application: `backend/app/main.py`
- API routes: `backend/app/api/routes/`
- Database models: `backend/app/models/`
- Services: `backend/app/services/`

To run backend only:
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

- Pages: `frontend/app/`
- Components: `frontend/components/`
- API client: `frontend/lib/api.ts`

To run frontend only:
```bash
cd frontend
npm run dev
```

## Environment Variables

See `.env.example` for all required environment variables. For a complete list of all environment variables, see [docs/deploy/RENDER_BACKEND_ENV_COMPLETE.md](docs/deploy/RENDER_BACKEND_ENV_COMPLETE.md).

### Required (Must Set)

#### Backend
- `DATABASE_URL` - PostgreSQL connection string
  - **Render:** Auto-wired from PostgreSQL database (no manual setup)
  - **Local:** `postgresql+asyncpg://user:pass@localhost:5432/dbname`
- `THE_ODDS_API_KEY` - The Odds API key ([get from the-odds-api.com](https://the-odds-api.com))
- `OPENAI_API_KEY` - OpenAI API key ([get from platform.openai.com](https://platform.openai.com))
- `JWT_SECRET` - JWT signing secret
  - **Render:** Auto-generated (no manual setup)
  - **Local:** Generate a secure random string
- `FRONTEND_URL` - Frontend domain (e.g., `https://www.parlaygorilla.com`)
- `BACKEND_URL` - Backend API domain (e.g., `https://api.parlaygorilla.com`)
- `APP_URL` - Same as FRONTEND_URL

#### Frontend
- `NEXT_PUBLIC_API_URL` - Backend API URL (default: `http://localhost:8000`)
- `PG_BACKEND_URL` - Optional backend URL for Next.js server-side rewrites (Render private-network hostport supported)

### Auto-Wired by Render (No Action Needed)

These are automatically configured when deploying via `render.yaml` Blueprint:

- `DATABASE_URL` - From PostgreSQL database
- `REDIS_URL` - From Key Value store
- `JWT_SECRET` - Auto-generated
- `ENVIRONMENT=production`
- `DEBUG=false`
- `USE_SQLITE=false`
- `OPENAI_ENABLED=true`

### Optional (Recommended for Production)

#### External APIs
- `SPORTSRADAR_API_KEY` - SportsRadar API for schedules, stats, injuries
- `OPENWEATHER_API_KEY` - Weather data for game analysis
- `PEXELS_API_KEY` - Team action photos
- `RESEND_API_KEY` - Email service (verification, password reset)

#### Payment Providers
- `LEMONSQUEEZY_API_KEY` - LemonSqueezy API key
- `LEMONSQUEEZY_STORE_ID` - LemonSqueezy store ID
- `LEMONSQUEEZY_WEBHOOK_SECRET` - LemonSqueezy webhook secret
- `LEMONSQUEEZY_PREMIUM_MONTHLY_VARIANT_ID` - Monthly subscription variant
- `LEMONSQUEEZY_PREMIUM_ANNUAL_VARIANT_ID` - Annual subscription variant
- `LEMONSQUEEZY_LIFETIME_VARIANT_ID` - Lifetime access variant
- `LEMONSQUEEZY_CREDITS_*_VARIANT_ID` - Credit pack variants (10, 25, 50, 100)
- `COINBASE_COMMERCE_API_KEY` - Coinbase Commerce API key
- `COINBASE_COMMERCE_WEBHOOK_SECRET` - Coinbase Commerce webhook secret

#### Blockchain (Inscriptions Worker)
- `SIGNER_PRIVATE_KEY` - Solana private key for inscriptions
- `RPC` - Solana RPC URL

#### Affiliate Payouts
- `PAYPAL_CLIENT_ID` - PayPal API client ID
- `PAYPAL_CLIENT_SECRET` - PayPal API client secret
- `CIRCLE_API_KEY` - Circle USDC API key
- `CIRCLE_ENVIRONMENT` - Circle environment (sandbox/production)

See [docs/deploy/RENDER_BACKEND_ENV_COMPLETE.md](docs/deploy/RENDER_BACKEND_ENV_COMPLETE.md) for the complete list with descriptions.

### Getting API Keys

1. **The Odds API:**
   - Sign up at [the-odds-api.com](https://the-odds-api.com)
   - Free tier provides 500 requests/month
   - Copy your API key from the dashboard

2. **OpenAI:**
   - Sign up at [platform.openai.com](https://platform.openai.com)
   - Add payment method (required for API access)
   - Create an API key in the API keys section

3. **Render (Production):**
   - Deploy using the repo's root `render.yaml` Blueprint
   - Render will provision PostgreSQL + Redis and wire `DATABASE_URL`/`REDIS_URL` automatically
   - See [docs/deploy/RENDER_SETUP_GUIDE.md](docs/deploy/RENDER_SETUP_GUIDE.md) for detailed deployment instructions

## Deployment

### Production Deployment (Render)

Parlay Gorilla is deployed on Render using the `render.yaml` Blueprint:

1. **Connect Repository:** Link your GitHub repo to Render
2. **Deploy Blueprint:** Render auto-detects `render.yaml` and creates all services
3. **Set Environment Variables:** Configure API keys and secrets in Render dashboard
4. **Run Migrations:** Execute `alembic upgrade head` in Render Shell
5. **Configure Domains:** Add custom domains in Render dashboard

**Services Created:**
- Frontend web service (`parlay-gorilla-frontend`)
- Backend web service (`parlay-gorilla-backend`)
- PostgreSQL database (`parlay-gorilla-postgres`)
- Redis Key Value store (`parlay-gorilla-redis`)
- Inscriptions worker (`parlay-gorilla-inscriptions-worker`)

**Auto-Configuration:**
- `DATABASE_URL` automatically wired from PostgreSQL
- `REDIS_URL` automatically wired from Key Value store
- `JWT_SECRET` automatically generated
- Frontend-backend communication via Render private network

See [docs/deploy/RENDER_SETUP_GUIDE.md](docs/deploy/RENDER_SETUP_GUIDE.md) for complete deployment guide.

### Local Development

**Backend:**
- Uses Docker PostgreSQL (via `docker-compose up -d postgres`)
- Or local PostgreSQL instance
- SQLite fallback available (set `USE_SQLITE=true`)

**Frontend:**
- Connects to backend via `NEXT_PUBLIC_API_URL`
- API calls proxied through Next.js rewrites

## Documentation

All documentation is organized in the `docs/` directory:

- **[Architecture](docs/architecture/)** - System architecture and technical details
- **[Deployment](docs/deploy/)** - Deployment guides and configuration
- **[Payments](docs/payments/)** - Payment processing and webhooks
- **[Troubleshooting](docs/troubleshooting/)** - Common issues and fixes
- **[Operations](docs/ops/)** - Development scripts and testing guides

See [docs/README.md](docs/README.md) for complete documentation index.

## Features

### ✅ Completed Features

#### Core Functionality
- ✅ Multi-sport support (NFL, NBA, NHL, MLB, Soccer, UFC, Boxing)
- ✅ AI-powered parlay generation (1-20 legs)
- ✅ Custom parlay builder with AI analysis
- ✅ Real-time odds fetching and updates
- ✅ Game analysis with win probabilities

#### Authentication & User Management
- ✅ Backend JWT authentication (no Supabase)
- ✅ User registration and login
- ✅ Email verification
- ✅ Password reset flow
- ✅ Protected routes and session management

#### Social Features
- ✅ Share parlays with unique links
- ✅ Social feed of shared parlays
- ✅ Like and comment on shared parlays
- ✅ Leaderboard of top performers

#### Advanced Parlay Types
- ✅ Same-game parlays
- ✅ Round-robin builder
- ✅ Teaser builder with point adjustments

#### Analytics & Monitoring
- ✅ Analytics dashboard
- ✅ Parlay performance tracking
- ✅ Application metrics endpoint
- ✅ Detailed health checks

### 🚀 Production Ready
- ✅ Environment variable validation
- ✅ Structured logging
- ✅ Error handling and validation
- ✅ Rate limiting
- ✅ CORS configuration
- ✅ CI/CD pipeline (GitHub Actions)

## License

Proprietary - Parlay Gorilla

## Troubleshooting

### Backend Issues

**Database Connection Errors:**
- Verify your `DATABASE_URL` is set correctly
- Ensure `USE_SQLITE=false` is set
- Check that your database password is correctly set
- Run `python scripts/verify_remote_database.py` to test connection

**The Odds API Errors:**
- Verify your API key is correct
- Check your API quota (free tier: 500 requests/month)
- Ensure you're using the correct endpoint format

**Import Errors:**
- Make sure you're in the `backend` directory when running commands
- Verify your virtual environment is activated
- Run `pip install -r requirements.txt` again

### Frontend Issues

**API Connection Errors:**
- Verify `NEXT_PUBLIC_API_URL` matches your backend URL
- Ensure the backend server is running
- Check CORS settings in `backend/app/main.py`

**Build Errors:**
- Delete `node_modules` and `.next` folder, then run `npm install` again
- Verify Node.js version is 18+

**Styling Issues:**
- Ensure Tailwind CSS is properly configured
- Check that `globals.css` is imported in `layout.tsx`

## Cost Optimization

To keep costs minimal (only paying for OpenAI):

1. **Use Free Tiers:**
   - Render Key Value (Redis): Free tier available
   - Render frontend can be run on the free web service plan (may spin down)

2. **Minimize API Calls:**
   - Odds are cached in database for 24 hours
   - Use `gpt-4o-mini` for most operations (cheaper than GPT-4)

3. **Rate Limiting:**
   - Implement rate limits for free users
   - Cache OpenAI responses when possible

## Disclaimer

This application is for entertainment and informational purposes only. It does not guarantee profits and should not be used as the sole basis for betting decisions. Always bet responsibly and never wager more than you can afford to lose.

