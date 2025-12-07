#!/bin/bash
# Production setup script for Parlay Gorilla

echo "=========================================="
echo "Parlay Gorilla - Production Setup"
echo "=========================================="

# Check if Neon URL is set
if [ -z "$NEON_DATABASE_URL" ]; then
    echo "Error: NEON_DATABASE_URL environment variable not set"
    echo "Please set it to your Neon connection string"
    exit 1
fi

# Set production environment
export ENVIRONMENT=production
export DATABASE_URL=$NEON_DATABASE_URL

echo ""
echo "1. Running database migrations..."
alembic upgrade head

echo ""
echo "2. Fetching live games..."
python fetch_live_games.py

echo ""
echo "=========================================="
echo "Production setup complete!"
echo "=========================================="

