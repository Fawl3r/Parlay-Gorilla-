# F3 Parlay AI Backend

FastAPI backend for the F3 Parlay AI application.

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables (copy `.env.example` to `.env`)

3. Run the development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── core/                 # Configuration and dependencies
│   ├── database/             # Database session management
│   ├── models/               # SQLAlchemy models
│   ├── schemas/              # Pydantic schemas
│   ├── api/                  # API route handlers
│   └── services/             # Business logic services
├── requirements.txt
└── .env.example
```

## Development

The application uses async SQLAlchemy with Supabase PostgreSQL. Database tables are automatically created on startup (use Alembic for production migrations).

