"""
Verify remote database connection and check if data is stored remotely.

This script helps ensure your database is configured for remote deployment (Render).
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.database.session import DATABASE_URL, engine
from sqlalchemy import text


async def verify_database():
    """Verify database connection and location"""
    print("\n" + "="*60)
    print("DATABASE CONNECTION VERIFICATION")
    print("="*60 + "\n")
    
    # Check configuration
    print("Configuration:")
    print(f"  Environment: {settings.environment}")
    print(f"  Database URL: {DATABASE_URL[:80]}...")
    print(f"  Using SQLite: {DATABASE_URL.startswith('sqlite')}")
    print(f"  Is Local: {'localhost' in DATABASE_URL or '127.0.0.1' in DATABASE_URL}")
    print(f"  Is Remote: {'render.com' in DATABASE_URL or 'amazonaws.com' in DATABASE_URL}")
    print()
    
    # Test connection
    print("Testing connection...")
    try:
        async with engine.connect() as conn:
            # Check if SQLite or PostgreSQL
            if DATABASE_URL.startswith('sqlite'):
                print(f"  [CRITICAL] Using SQLite (local file database)")
                print(f"  SQLite will NOT work on Render - you MUST use PostgreSQL")
                print(f"  Database file: {DATABASE_URL.split('///')[-1] if '///' in DATABASE_URL else 'N/A'}")
            else:
                # PostgreSQL-specific queries
                result = await conn.execute(text("SELECT version(), current_database(), inet_server_addr(), inet_server_port()"))
                row = result.fetchone()
                
                if row:
                    version = row[0]
                    db_name = row[1]
                    server_addr = row[2]  # Will be None for local connections
                    server_port = row[3]
                    
                    print(f"  ✓ Connected successfully!")
                    print(f"  PostgreSQL Version: {version.split(',')[0]}")
                    print(f"  Database Name: {db_name}")
                    
                    if server_addr:
                        print(f"  Server Address: {server_addr}:{server_port}")
                        print(f"  [OK] REMOTE DATABASE CONFIRMED")
                    else:
                        print(f"  Server Address: localhost (local connection)")
                        print(f"  [WARNING] Using local database - not suitable for Render deployment")
                
            # Check if we have data (works for both SQLite and PostgreSQL)
            print("\nChecking stored data...")
            try:
                result = await conn.execute(text("""
                    SELECT 
                        (SELECT COUNT(*) FROM games) as games_count,
                        (SELECT COUNT(*) FROM game_results) as results_count,
                        (SELECT COUNT(*) FROM team_stats) as stats_count,
                        (SELECT COUNT(*) FROM game_analyses) as analyses_count
                """))
                data_row = result.fetchone()
                
                if data_row:
                    print(f"  Games: {data_row[0]}")
                    print(f"  Game Results: {data_row[1]}")
                    print(f"  Team Stats: {data_row[2]}")
                    print(f"  Analyses: {data_row[3]}")
                    
                    total = sum(data_row)
                    if total > 0:
                        print(f"\n  [OK] Database contains {total} total records")
                        if DATABASE_URL.startswith('sqlite'):
                            print(f"  [WARNING] This data is in SQLite - it will NOT transfer to Render")
                            print(f"  You need to migrate to remote PostgreSQL and re-run backfill")
                    else:
                        print(f"\n  [WARNING] Database is empty - run backfill script after switching to PostgreSQL")
            except Exception as data_error:
                print(f"  [WARNING] Could not check data: {data_error}")
                print(f"  Tables may not exist yet - run migrations first")
        
    except Exception as e:
        print(f"  [ERROR] Connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*60)
    print("RECOMMENDATIONS FOR RENDER DEPLOYMENT")
    print("="*60)
    
    if DATABASE_URL.startswith('sqlite'):
        print("\n[CRITICAL] You're using SQLite (local file database)")
        print("  SQLite will NOT work on Render - you need PostgreSQL")
        print("\n  Action required:")
        print("  1. Set up a remote PostgreSQL database (Render PostgreSQL recommended)")
        print("  2. Update DATABASE_URL in .env to point to remote database")
        print("  3. Set USE_SQLITE=false in .env")
        print("  4. Run migrations: alembic upgrade head")
        print("  5. Run backfill: python scripts/backfill_all_sports_data.py")
    
    elif 'localhost' in DATABASE_URL or '127.0.0.1' in DATABASE_URL:
        print("\n[WARNING] You're using local PostgreSQL")
        print("  Local database will NOT be accessible from Render")
        print("\n  Action required:")
        print("  1. Set up a remote PostgreSQL database (Render PostgreSQL recommended)")
        print("  2. Update DATABASE_URL in .env to remote connection string")
        print("  3. For production, set ENVIRONMENT=production")
        print("  4. Run migrations on remote database")
        print("  5. Run backfill to populate remote database")
    
    else:
        print("\n[OK] You're using a remote database!")
        print("  Your data is stored remotely and ready for Render deployment")
        print("\n  Next steps:")
        print("  1. Ensure ENVIRONMENT=production in Render environment variables")
        print("  2. Set DATABASE_URL in Render dashboard (or use the repo’s render.yaml Blueprint)")
        print("  3. Deploy to Render - your data will persist")
    
    print("\n" + "="*60 + "\n")
    return True


if __name__ == "__main__":
    asyncio.run(verify_database())

