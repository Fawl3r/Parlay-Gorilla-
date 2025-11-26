# F3 Parlay AI – 20-Leg Predictive Parlay Engine

An AI-powered sports betting assistant that generates 1–20 leg parlays with win probabilities, confidence scores, and detailed explanations.

## Project Structure

This is a monorepo containing:

- `backend/` - FastAPI application for odds fetching, predictions, and parlay generation
- `frontend/` - Next.js application for the user interface

## Tech Stack

### Backend
- **Framework:** FastAPI
- **Database:** Supabase (PostgreSQL)
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
- Supabase account (free tier)
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
   - `DATABASE_URL`: Your Supabase PostgreSQL connection string
   - `THE_ODDS_API_KEY`: Your The Odds API key
   - `OPENAI_API_KEY`: Your OpenAI API key

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

### Supabase Configuration

1. Create a new project on [Supabase](https://supabase.com)
2. **Option A - Using Supabase CLI (Recommended):**
   ```bash
   # Install Supabase CLI
   npm install -g supabase
   
   # Login
   supabase login
   
   # Link your project (from backend directory)
   cd backend
   supabase link --project-ref your-project-ref
   
   # Get connection string
   supabase status
   ```
   - Find your project ref in Supabase dashboard (Settings → General → Reference ID)

3. **Option B - Using Dashboard:**
   - Go to Settings → Database
   - Copy the connection string (use the "URI" format)
   - Replace `[YOUR-PASSWORD]` with your database password
   - **Important:** Add `+asyncpg` after `postgresql` (e.g., `postgresql+asyncpg://...`)

4. Update your `DATABASE_URL` in `backend/.env`

**Important:** The connection string must include `+asyncpg` for async SQLAlchemy:
```
DATABASE_URL=postgresql+asyncpg://postgres.xxx:password@host:port/database
```

The database schema will be automatically created on first run (or you can use Alembic migrations in the future).

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
    "service": "F3 Parlay AI API"
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

### Backend Development

- Main application: `backend/app/main.py`
- API routes: `backend/app/api/routes/`
- Database models: `backend/app/models/`
- Services: `backend/app/services/`

### Frontend Development

- Pages: `frontend/app/`
- Components: `frontend/components/`
- API client: `frontend/lib/api.ts`

## Environment Variables

See `.env.example` for all required environment variables.

### Backend Variables
- `DATABASE_URL` - Supabase PostgreSQL connection string (format: `postgresql+asyncpg://user:password@host:port/database`)
- `THE_ODDS_API_KEY` - The Odds API key (get from [the-odds-api.com](https://the-odds-api.com))
- `OPENAI_API_KEY` - OpenAI API key (get from [platform.openai.com](https://platform.openai.com))
- `BACKEND_URL` - Backend API URL (default: `http://localhost:8000`)

### Frontend Variables
- `NEXT_PUBLIC_API_URL` - Backend API URL (default: `http://localhost:8000`)

### Getting API Keys

1. **The Odds API:**
   - Sign up at [the-odds-api.com](https://the-odds-api.com)
   - Free tier provides 500 requests/month
   - Copy your API key from the dashboard

2. **OpenAI:**
   - Sign up at [platform.openai.com](https://platform.openai.com)
   - Add payment method (required for API access)
   - Create an API key in the API keys section

3. **Supabase:**
   - Sign up at [supabase.com](https://supabase.com)
   - Create a new project
   - **Using CLI (Recommended):**
     ```bash
     npm install -g supabase
     supabase login
     supabase link --project-ref your-project-ref
     supabase status  # Shows connection string
     ```
   - **Or using Dashboard:**
     - Go to Settings → Database → Connection string
     - Use the "URI" format and replace `[YOUR-PASSWORD]` with your database password
     - **Important:** Add `+asyncpg` after `postgresql` in the connection string

## Project Roadmap

### Phase 1 (Current)
- ✅ Basic project structure
- ✅ Odds fetching from The Odds API
- ✅ Database models for games, markets, odds
- ✅ Basic UI showing upcoming games

### Phase 2 (Next)
- Basic parlay engine with heuristic probabilities
- OpenAI-powered explanations
- Parlay builder UI

### Phase 3
- User authentication
- Subscription tiers
- Monetization

### Phase 4
- ML model integration
- Advanced probability calibration
- Multi-sport support

## License

Proprietary - F3 AI Labs

## Troubleshooting

### Backend Issues

**Database Connection Errors:**
- Verify your `DATABASE_URL` is correct and includes `+asyncpg` driver
- Ensure your Supabase project is active
- Check that your database password is correctly set

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
   - Supabase: Free tier includes 500MB database
   - Vercel: Free tier for frontend hosting
   - Render/Railway: Free tier for backend (with limitations)

2. **Minimize API Calls:**
   - Odds are cached in database for 24 hours
   - Use `gpt-4o-mini` for most operations (cheaper than GPT-4)

3. **Rate Limiting:**
   - Implement rate limits for free users
   - Cache OpenAI responses when possible

## Disclaimer

This application is for entertainment and informational purposes only. It does not guarantee profits and should not be used as the sole basis for betting decisions. Always bet responsibly and never wager more than you can afford to lose.

