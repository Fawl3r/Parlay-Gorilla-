#!/usr/bin/env python3
"""Fix migration 028 by manually marking it as applied if tables already exist.

This script checks if the arcade_points tables exist, and if so, marks the migration
as applied in the alembic_version table.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings


def check_table_exists(conn, table_name: str) -> bool:
    """Check if a table exists in the database."""
    result = conn.execute(text(
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = :name)"
    ), {"name": table_name})
    return result.scalar()


def check_migration_applied(conn, revision: str) -> bool:
    """Check if a migration revision is already applied."""
    result = conn.execute(text(
        "SELECT EXISTS (SELECT FROM alembic_version WHERE version_num = :revision)"
    ), {"revision": revision})
    return result.scalar()


def main():
    """Main function."""
    print("=" * 60)
    print("Fix Migration 028 - Arcade Points Tables")
    print("=" * 60)
    print()
    
    # Create database connection
    engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        # Check if tables exist
        events_exists = check_table_exists(conn, "arcade_points_events")
        totals_exists = check_table_exists(conn, "arcade_points_totals")
        migration_applied = check_migration_applied(conn, "028_add_arcade_points_tables")
        
        print(f"Table 'arcade_points_events' exists: {events_exists}")
        print(f"Table 'arcade_points_totals' exists: {totals_exists}")
        print(f"Migration 028 already applied: {migration_applied}")
        print()
        
        if events_exists and totals_exists:
            if not migration_applied:
                print("✅ Tables exist but migration not marked as applied.")
                print("   Marking migration 028 as applied...")
                
                # Insert migration version
                conn.execute(text(
                    "INSERT INTO alembic_version (version_num) VALUES (:revision) ON CONFLICT DO NOTHING"
                ), {"revision": "028_add_arcade_points_tables"})
                conn.commit()
                
                print("✅ Migration 028 marked as applied!")
                print()
                print("Next steps:")
                print("  1. Run: alembic upgrade head")
                print("  2. This should now skip migration 028 and continue with later migrations")
                return 0
            else:
                print("✅ Tables exist and migration is already marked as applied.")
                print("   You can proceed with: alembic upgrade head")
                return 0
        elif not events_exists and not totals_exists:
            print("❌ Tables do not exist. Migration 028 needs to run normally.")
            print("   The fixed migration code should handle this now.")
            print("   Try running: alembic upgrade head")
            return 1
        else:
            print("⚠️  Partial state detected:")
            print(f"   - arcade_points_events: {events_exists}")
            print(f"   - arcade_points_totals: {totals_exists}")
            print("   This is unexpected. Please check the database manually.")
            return 1


if __name__ == "__main__":
    sys.exit(main())
