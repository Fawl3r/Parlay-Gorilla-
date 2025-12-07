"""
Migration script to move from SQLite to PostgreSQL
Run this after setting up Docker PostgreSQL
"""
import asyncio
import os

# Force PostgreSQL mode
os.environ["USE_SQLITE"] = "false"

async def migrate_to_postgres():
    """Migrate database from SQLite to PostgreSQL"""
    print("=" * 60)
    print("Parlay Gorilla - PostgreSQL Migration")
    print("=" * 60)
    
    from app.database.session import engine, Base, DATABASE_URL
    from app.models import *
    
    print(f"\nTarget Database: {DATABASE_URL}")
    print("\n1. Creating all tables in PostgreSQL...")
    
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("   ✓ Tables created successfully!")
    except Exception as e:
        print(f"   ✗ Error creating tables: {e}")
        return
    
    # If SQLite database exists, offer to migrate data
    sqlite_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "parlay_gorilla.db")
    if os.path.exists(sqlite_path):
        print(f"\n2. Found SQLite database at {sqlite_path}")
        migrate_data = input("   Migrate data from SQLite? (y/n): ").lower() == 'y'
        
        if migrate_data:
            print("   Migrating data...")
            # This would require sqlite3 and asyncpg to copy data
            # For now, just note that data needs to be re-fetched
            print("   Note: Data migration not implemented. Run fetch_live_games.py to populate.")
    else:
        print("\n2. No SQLite database found. Starting fresh.")
        print("   Run fetch_live_games.py to populate with live data.")
    
    print("\n" + "=" * 60)
    print("Migration complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Run: python fetch_live_games.py")
    print("  2. Run: alembic revision --autogenerate -m 'initial'")
    print("  3. Run: alembic upgrade head")


if __name__ == "__main__":
    asyncio.run(migrate_to_postgres())

