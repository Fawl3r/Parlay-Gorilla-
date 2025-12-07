# Parlay Gorilla Backend

## Quick Start

### 1. Start Docker PostgreSQL

```bash
docker-compose up -d postgres
```

This will start:
- PostgreSQL on `localhost:5432`
- Redis on `localhost:6379`

### 2. Configure Environment

Copy `.env` and update with your keys:
- `THE_ODDS_API_KEY` - Your Odds API key
- `OPENAI_API_KEY` - Your OpenAI API key

### 3. Initialize Database

```bash
python setup_database.py
```

### 4. Fetch Live Games

```bash
python fetch_live_games.py
```

### 5. Start Backend Server

```bash
python -m uvicorn app.main:app --reload --port 8000
```

## Database Configuration

### Local Development (Docker)
- Connection: `postgresql+asyncpg://devuser:devpass@localhost:5432/parlaygorilla`
- Auto-configured in `.env`

### Production (Neon)
1. Create project at https://neon.tech
2. Copy connection string
3. Add to `.env` as `NEON_DATABASE_URL`
4. Set `ENVIRONMENT=production`

## API Endpoints

- `GET /health` - Health check
- `GET /api/sports/{sport}/games` - Get games for a sport
- `POST /api/parlay/suggest` - Generate parlay
- `GET /api/analysis/{sport}/upcoming` - List analyses
- `POST /api/analysis/generate` - Generate analysis

## Background Jobs

Configured via APScheduler:
- Odds sync every 5 minutes
- Scraper runs every 30 minutes
- Analysis generation daily at 6 AM
