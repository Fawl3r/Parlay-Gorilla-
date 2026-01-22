#!/usr/bin/env python3
"""Diagnose and fix Alembic migration issues.

This script helps diagnose why Alembic can't locate a revision.
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from app.core.config import settings


def check_database_state():
    """Check the current state of the database and alembic_version table."""
    print("=" * 60)
    print("Database Migration Diagnostic")
    print("=" * 60)
    
    # Get database URL
    if settings.use_sqlite:
        print("❌ This script is for PostgreSQL only")
        return
    
    db_url = (
        settings.database_url
        .replace("postgresql+asyncpg://", "postgresql://", 1)
        .replace("postgres://", "postgresql://", 1)
    )
    
    engine = create_engine(db_url)
    
    try:
        with engine.connect() as conn:
            # Check alembic_version table
            print("\n1. Checking alembic_version table...")
            result = conn.execute(text("SELECT version_num FROM alembic_version ORDER BY version_num"))
            versions = [row[0] for row in result]
            
            if versions:
                print(f"   Current revision in database: {versions[-1]}")
                print(f"   All revisions: {', '.join(versions)}")
            else:
                print("   ⚠️  No revisions found in alembic_version table")
            
            # Check if migration 035 tables exist
            print("\n2. Checking if migration 035 tables exist...")
            tables_to_check = [
                "team_stats_snapshots",
                "injury_snapshots",
                "team_stats_current",
                "injury_current",
                "team_features_current",
            ]
            
            for table in tables_to_check:
                result = conn.execute(
                    text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = :table_name
                        )
                    """),
                    {"table_name": table}
                )
                exists = result.scalar()
                status = "✅" if exists else "❌"
                print(f"   {status} {table}: {'exists' if exists else 'missing'}")
            
            # Recommendations
            print("\n3. Recommendations:")
            if "035_add_stats_platform_tables" in versions:
                print("   ⚠️  Revision 035 is recorded in database")
                all_exist = all(
                    conn.execute(
                        text("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables 
                                WHERE table_schema = 'public' 
                                AND table_name = :table_name
                            )
                        """),
                        {"table_name": table}
                    ).scalar()
                    for table in tables_to_check
                )
                if all_exist:
                    print("   ✅ All tables exist - migration was applied")
                    print("   💡 The error might be due to file not being found during deployment")
                else:
                    print("   ❌ Tables are missing - migration was not fully applied")
                    print("   💡 You may need to manually apply the migration or fix the database state")
            else:
                print("   ℹ️  Revision 035 is not in database")
                print("   💡 Migration should be able to run normally")
            
    except Exception as e:
        print(f"\n❌ Error connecting to database: {e}")
        return


if __name__ == "__main__":
    check_database_state()
