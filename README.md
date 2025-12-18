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
- **External APIs:** The Odds API, OpenAI

### Frontend
- **Framework:** Next.js 14+ (App Router)
- **Styling:** Tailwind CSS
- **Components:** shadcn/ui
- **Language:** TypeScript

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

## API Endpoints

### Health Check
- **Endpoint:** `GET /health`
- **Description:** Returns API health status
- **Response:**
  ```json
  {
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00",
    "service": "Parlay Gorilla API"
  }
  ```

### Games
- **Endpoint:** `GET /api/sports/nfl/games`
- **Description:** List upcoming NFL games with odds from The Odds API
- **Response:** Array of game objects with markets and odds
  ```json
  [
    {
      "id": "uuid",
      "external_game_id": "string",
      "sport": "NFL",
      "home_team": "Team Name",
      "away_team": "Team Name",
      "start_time": "2024-01-15T18:00:00Z",
      "status": "scheduled",
      "markets": [
        {
          "id": "uuid",
          "market_type": "h2h",
          "book": "draftkings",
          "odds": [
            {
              "id": "uuid",
              "outcome": "home",
              "price": "-110",
              "decimal_price": 1.909,
              "implied_prob": 0.524,
              "created_at": "2024-01-15T10:00:00Z"
            }
          ]
        }
      ]
    }
  ]
  ```
- **Notes:**
  - Games are automatically fetched from The Odds API if none exist in the database
  - Data is cached for 24 hours to minimize API calls
  - Market types: `h2h` (moneyline), `spreads`, `totals`

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

See `.env.example` for all required environment variables.

### Backend Variables
- `DATABASE_URL` - PostgreSQL connection string (Render PostgreSQL in production, local Postgres in dev)
- `USE_SQLITE` - Set to `true` to use SQLite fallback (default: `false`)
- `REDIS_URL` - Redis URL (required in production)
- `THE_ODDS_API_KEY` - The Odds API key (get from [the-odds-api.com](https://the-odds-api.com))
- `OPENAI_API_KEY` - OpenAI API key (get from [platform.openai.com](https://platform.openai.com))
- `JWT_SECRET` - JWT signing secret
- `BACKEND_URL` - Backend API URL (default: `http://localhost:8000`)

### Frontend Variables
- `NEXT_PUBLIC_API_URL` - Backend API URL (default: `http://localhost:8000`)
- `PG_BACKEND_URL` - Optional backend URL for Next.js server-side rewrites (Render private-network hostport supported)

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
   - Deploy using the repo’s root `render.yaml` Blueprint
   - Render will provision PostgreSQL + Redis and wire `DATABASE_URL`/`REDIS_URL` automatically
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

