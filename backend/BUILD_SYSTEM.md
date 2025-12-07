# Parlay Gorilla - Complete Build System

## 🏗️ Architecture Overview

### Backend Stack
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL (Docker local, Neon production)
- **ORM**: SQLAlchemy with Alembic migrations
- **Background Jobs**: APScheduler
- **AI**: OpenAI GPT-4o-mini
- **APIs**: The Odds API, ESPN, Covers.com, Rotowire

### Frontend Stack
- **Framework**: Next.js 14 (React)
- **Styling**: Tailwind CSS
- **Animations**: Framer Motion
- **Auth**: Supabase Auth

## 📁 Folder Structure

```
backend/
├── alembic/                    # Database migrations
│   ├── versions/              # Migration files
│   └── env.py                # Alembic config
├── app/
│   ├── api/
│   │   └── routes/           # API endpoints
│   │       ├── parlay.py     # Basic parlay routes
│   │       ├── parlay_extended.py  # 20-leg, history
│   │       ├── team_stats.py # Team stats API
│   │       ├── scraper.py    # Scraper triggers
│   │       └── user.py       # User management
│   ├── models/               # SQLAlchemy models
│   ├── schemas/              # Pydantic schemas
│   ├── services/             # Business logic
│   │   ├── parlay_builder.py # Parlay generation
│   │   ├── odds_fetcher.py   # Odds API integration
│   │   ├── stats_scraper.py   # Web scraping
│   │   ├── analysis_generator.py  # AI analysis
│   │   └── scheduler.py      # Background jobs
│   ├── workers/              # Background workers
│   │   ├── scraper_worker.py
│   │   ├── odds_sync_worker.py
│   │   └── ai_model_trainer.py
│   ├── database/             # DB session & config
│   └── core/                 # Config & dependencies
├── scripts/                   # Utility scripts
│   ├── setup_database.py
│   ├── fetch_live_games.py
│   └── migrate_to_postgres.py
├── docker-compose.yml        # Docker setup
└── alembic.ini              # Alembic config

frontend/
├── app/
│   ├── page.tsx             # Public landing page
│   ├── app/                 # Protected app
│   │   └── page.tsx        # Main app (requires auth)
│   └── auth/               # Auth pages
├── components/
│   ├── analysis/           # Analysis components
│   └── ads/               # Ad slots
└── lib/
    ├── api.ts             # API client
    └── auth-context.tsx   # Auth context
```

## 🚀 Quick Start

### Local Development

1. **Start Docker PostgreSQL**
   ```bash
   cd backend
   docker-compose up -d postgres
   ```

2. **Configure Environment**
   ```bash
   # Edit .env
   USE_SQLITE=false
   DATABASE_URL=postgresql+asyncpg://devuser:devpass@localhost:5432/parlaygorilla
   ```

3. **Run Migrations**
   ```bash
   alembic revision --autogenerate -m "initial"
   alembic upgrade head
   ```

4. **Populate Database**
   ```bash
   python fetch_live_games.py
   ```

5. **Start Backend**
   ```bash
   python -m uvicorn app.main:app --reload --port 8000
   ```

6. **Start Frontend**
   ```bash
   cd frontend
   npm run dev
   ```

### Production (Neon)

1. **Create Neon Project**
   - Go to https://neon.tech
   - Create project
   - Copy connection string

2. **Configure Production**
   ```bash
   export NEON_DATABASE_URL="postgresql://user:pass@ep-xxx.neon.tech/parlaygorilla?sslmode=require"
   export ENVIRONMENT=production
   ```

3. **Deploy**
   ```bash
   # Run migrations
   alembic upgrade head
   
   # Fetch initial data
   python fetch_live_games.py
   ```

## 📡 API Endpoints

### Parlay Routes
- `POST /api/parlay/suggest` - Generate parlay (1-20 legs)
- `POST /api/parlay/20-leg` - Generate 20-leg parlay
- `GET /api/parlay/history/{user_id}` - Get parlay history
- `GET /api/parlay/history` - Get current user's history

### Games & Odds
- `GET /api/sports/{sport}/games` - Get games for sport
- `GET /api/odds/{sport}` - Get odds for sport

### Team Stats
- `GET /api/team-stats/{sport}/{team}` - Get team statistics

### Scraper
- `POST /api/scraper/update` - Trigger scraper update
- `POST /api/scraper/update-stats` - Update team stats

### User
- `POST /api/user/register` - Register user
- `POST /api/user/upgrade` - Upgrade to premium

### Analysis
- `GET /api/analysis/{sport}/upcoming` - List analyses
- `GET /api/analysis/{sport}/{slug}` - Get analysis
- `POST /api/analysis/generate` - Generate analysis

## 🔄 Background Workers

### Scheduled Jobs (APScheduler)

1. **Odds Sync** - Every 5 minutes
   - Syncs live odds from The Odds API
   - Updates markets and odds

2. **Scraper Worker** - Every 30 minutes
   - Scrapes team stats from ESPN/Covers
   - Updates injury reports
   - Fetches weather data

3. **AI Model Trainer** - Daily at 2 AM
   - Analyzes parlay performance
   - Updates model weights
   - Trains on game results

4. **Analysis Generator** - Daily at 6 AM
   - Generates AI analyses for upcoming games
   - Creates SEO-optimized content

5. **Cache Cleanup** - Daily at 2 AM
   - Removes expired cache entries

6. **Parlay Resolution** - Every 6 hours
   - Auto-resolves completed parlays

## 🤖 AI Pipeline

```
Odds API → Stat Scraper → Feature Builder → AI Model → Parlay Generator
```

### Components:
1. **Odds Fetcher** - Gets live odds from The Odds API
2. **Stats Scraper** - Fetches team stats, injuries, weather
3. **Feature Builder** - Combines odds + stats into features
4. **AI Model** - OpenAI GPT-4o-mini for predictions
5. **Parlay Generator** - Creates 1-20 leg parlays with confidence scores

### Confidence Scoring:
- **Conservative**: Min 70% confidence per leg
- **Balanced**: Min 55% confidence per leg
- **Degen**: Min 40% confidence per leg

## 📊 Database Schema

### Core Tables
- `games` - Sports games/matches
- `markets` - Betting markets (spread, total, moneyline)
- `odds` - Odds for market outcomes
- `parlays` - Generated parlay suggestions
- `parlay_results` - Parlay outcomes
- `team_stats` - Team statistics
- `game_results` - Actual game outcomes
- `game_analyses` - AI-generated analyses
- `users` - User accounts

## 🔧 Development Workflow

### Making Schema Changes

1. **Update Model**
   ```python
   # app/models/your_model.py
   # Add/modify columns
   ```

2. **Generate Migration**
   ```bash
   alembic revision --autogenerate -m "add_new_field"
   ```

3. **Review Migration**
   ```bash
   # Check alembic/versions/xxx_add_new_field.py
   ```

4. **Apply Migration**
   ```bash
   alembic upgrade head
   ```

### Adding New API Route

1. Create route file: `app/api/routes/new_route.py`
2. Add to `app/api/routes/__init__.py`
3. Include in `app/main.py`:
   ```python
   app.include_router(new_route.router, prefix="/api", tags=["New"])
   ```

### Adding Background Job

1. Create worker: `app/workers/new_worker.py`
2. Add to scheduler in `app/services/scheduler.py`:
   ```python
   self.scheduler.add_job(
       self._run_new_worker,
       IntervalTrigger(minutes=30),
       id="new_worker",
   )
   ```

## 🧪 Testing

```bash
# Backend tests
pytest backend/tests/

# Frontend type check
cd frontend && npx tsc --noEmit

# Frontend build
cd frontend && npm run build
```

## 📝 Environment Variables

### Backend (.env)
```env
ENVIRONMENT=development
DATABASE_URL=postgresql+asyncpg://devuser:devpass@localhost:5432/parlaygorilla
NEON_DATABASE_URL=postgresql://user:pass@ep-xxx.neon.tech/parlaygorilla?sslmode=require
USE_SQLITE=false
THE_ODDS_API_KEY=your_key
OPENAI_API_KEY=your_key
REDIS_URL=redis://localhost:6379
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_key
```

## 🚢 Deployment

### Backend (Railway/Fly.io)
1. Set environment variables
2. Run migrations: `alembic upgrade head`
3. Deploy application

### Frontend (Vercel)
1. Connect GitHub repo
2. Set environment variables
3. Deploy automatically

### Database (Neon)
1. Create project
2. Copy connection string
3. Run migrations
4. Populate with initial data

