-- Parlay Gorilla Database Initialization Script
-- This runs automatically when the Docker PostgreSQL container starts

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create custom types
DO $$ BEGIN
    CREATE TYPE risk_profile AS ENUM ('conservative', 'balanced', 'degen');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE game_status AS ENUM ('scheduled', 'in_progress', 'final', 'cancelled', 'postponed');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE bet_result AS ENUM ('pending', 'won', 'lost', 'push', 'cancelled');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE parlaygorilla TO devuser;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Parlay Gorilla database initialized successfully!';
END $$;

