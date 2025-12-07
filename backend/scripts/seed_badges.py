"""
Seed starter badges into the database.

Run with: python scripts/seed_badges.py
"""

import asyncio
import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.database.session import AsyncSessionLocal
from app.models.badge import Badge, STARTER_BADGES
from sqlalchemy.exc import OperationalError


async def seed_badges():
    """Seed the starter badges into the database."""
    async with AsyncSessionLocal() as session:
        print("Seeding badges...")
        
        created_count = 0
        updated_count = 0
        
        try:
            for badge_data in STARTER_BADGES:
                # Check if badge already exists by slug
                result = await session.execute(
                    select(Badge).where(Badge.slug == badge_data["slug"])
                )
                existing_badge = result.scalar_one_or_none()
                
                if existing_badge:
                    # Update existing badge
                    existing_badge.name = badge_data["name"]
                    existing_badge.description = badge_data["description"]
                    existing_badge.icon = badge_data["icon"]
                    existing_badge.requirement_type = badge_data["requirement_type"]
                    existing_badge.requirement_value = badge_data["requirement_value"]
                    existing_badge.display_order = badge_data["display_order"]
                    updated_count += 1
                    print(f"  Updated: {badge_data['name']} ({badge_data['slug']})")
                else:
                    # Create new badge
                    badge = Badge(
                        id=uuid.uuid4(),
                        slug=badge_data["slug"],
                        name=badge_data["name"],
                        description=badge_data["description"],
                        icon=badge_data["icon"],
                        requirement_type=badge_data["requirement_type"],
                        requirement_value=badge_data["requirement_value"],
                        display_order=badge_data["display_order"],
                        is_active="1",
                    )
                    session.add(badge)
                    created_count += 1
                    print(f"  Created: {badge_data['name']} ({badge_data['slug']})")
            
            await session.commit()
            
            print(f"\nDone! Created {created_count} badges, updated {updated_count} badges.")
            print(f"Total badges: {len(STARTER_BADGES)}")
        except OperationalError as e:
            if "no such table" in str(e).lower():
                print("\n❌ Error: Database tables don't exist yet.")
                print("Please run the migration first:")
                print("  alembic upgrade head")
                print("\nIf using SQLite, you may need to switch to PostgreSQL or")
                print("ensure the migration has been applied to your SQLite database.")
                raise
            else:
                raise


async def list_badges():
    """List all badges in the database."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Badge).order_by(Badge.display_order)
        )
        badges = result.scalars().all()
        
        print(f"\n{'='*60}")
        print(f"{'Badge Inventory':^60}")
        print(f"{'='*60}\n")
        
        if not badges:
            print("No badges found in database.")
            return
        
        for badge in badges:
            print(f"{badge.icon} {badge.name} ({badge.slug})")
            print(f"   Requirement: {badge.requirement_type} >= {badge.requirement_value}")
            print(f"   Description: {badge.description}")
            print(f"   Display Order: {badge.display_order}")
            print()


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Badge seeding utility")
    parser.add_argument("--list", action="store_true", help="List all badges")
    args = parser.parse_args()
    
    if args.list:
        await list_badges()
    else:
        await seed_badges()
        await list_badges()


if __name__ == "__main__":
    asyncio.run(main())

