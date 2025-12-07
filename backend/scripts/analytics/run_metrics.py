#!/usr/bin/env python3
"""
CLI tool for running analytics queries.

Usage:
    python run_metrics.py [category] [--format json|table]
    
Categories:
    users     - User metrics (DAU/WAU/MAU, signups, etc.)
    usage     - Feature usage metrics
    revenue   - Revenue and subscription metrics
    model     - Model performance metrics
    all       - Run all metrics

Examples:
    python run_metrics.py users
    python run_metrics.py revenue --format json
    python run_metrics.py all
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func, text


async def get_db_session() -> AsyncSession:
    """Create a database session."""
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/parlay_gorilla"
    )
    
    # Convert to async URL if needed
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    return async_session()


async def get_user_metrics(db: AsyncSession) -> Dict[str, Any]:
    """Fetch user metrics."""
    now = datetime.utcnow()
    
    # Total users
    result = await db.execute(text("SELECT COUNT(*) FROM users"))
    total_users = result.scalar()
    
    # DAU
    result = await db.execute(text("""
        SELECT COUNT(DISTINCT id) FROM users 
        WHERE last_login >= NOW() - INTERVAL '24 hours'
    """))
    dau = result.scalar()
    
    # WAU
    result = await db.execute(text("""
        SELECT COUNT(DISTINCT id) FROM users 
        WHERE last_login >= NOW() - INTERVAL '7 days'
    """))
    wau = result.scalar()
    
    # MAU
    result = await db.execute(text("""
        SELECT COUNT(DISTINCT id) FROM users 
        WHERE last_login >= NOW() - INTERVAL '30 days'
    """))
    mau = result.scalar()
    
    # Users by plan
    result = await db.execute(text("""
        SELECT plan, COUNT(*) as count FROM users GROUP BY plan
    """))
    users_by_plan = {row[0]: row[1] for row in result.all()}
    
    # New users (last 7 days)
    result = await db.execute(text("""
        SELECT COUNT(*) FROM users 
        WHERE created_at >= NOW() - INTERVAL '7 days'
    """))
    new_users_7d = result.scalar()
    
    return {
        "total_users": total_users,
        "dau": dau,
        "wau": wau,
        "mau": mau,
        "users_by_plan": users_by_plan,
        "new_users_7d": new_users_7d,
    }


async def get_usage_metrics(db: AsyncSession) -> Dict[str, Any]:
    """Fetch usage metrics."""
    # Event counts
    result = await db.execute(text("""
        SELECT event_type, COUNT(*) as count 
        FROM app_events 
        WHERE created_at >= NOW() - INTERVAL '7 days'
        GROUP BY event_type
        ORDER BY count DESC
    """))
    event_counts = {row[0]: row[1] for row in result.all()}
    
    # Parlay stats
    result = await db.execute(text("""
        SELECT 
            COUNT(*) as total,
            ROUND(AVG(legs_count)::numeric, 2) as avg_legs,
            MIN(legs_count) as min_legs,
            MAX(legs_count) as max_legs
        FROM parlay_events
        WHERE created_at >= NOW() - INTERVAL '7 days'
    """))
    parlay_row = result.first()
    parlay_stats = {
        "total": parlay_row[0] if parlay_row else 0,
        "avg_legs": float(parlay_row[1]) if parlay_row and parlay_row[1] else 0,
        "min_legs": parlay_row[2] if parlay_row else 0,
        "max_legs": parlay_row[3] if parlay_row else 0,
    }
    
    # Unique sessions
    result = await db.execute(text("""
        SELECT COUNT(DISTINCT session_id) 
        FROM app_events 
        WHERE created_at >= NOW() - INTERVAL '7 days'
          AND session_id IS NOT NULL
    """))
    unique_sessions = result.scalar()
    
    return {
        "event_counts": event_counts,
        "parlay_stats": parlay_stats,
        "unique_sessions_7d": unique_sessions,
    }


async def get_revenue_metrics(db: AsyncSession) -> Dict[str, Any]:
    """Fetch revenue metrics."""
    # Total revenue
    result = await db.execute(text("""
        SELECT COALESCE(SUM(amount), 0), COUNT(*) 
        FROM payments 
        WHERE status = 'paid'
    """))
    row = result.first()
    total_revenue = float(row[0]) if row else 0
    total_payments = row[1] if row else 0
    
    # Revenue last 30 days
    result = await db.execute(text("""
        SELECT COALESCE(SUM(amount), 0) 
        FROM payments 
        WHERE status = 'paid' 
          AND paid_at >= NOW() - INTERVAL '30 days'
    """))
    revenue_30d = float(result.scalar() or 0)
    
    # Active subscriptions
    result = await db.execute(text("""
        SELECT COUNT(*) FROM subscriptions WHERE status = 'active'
    """))
    active_subs = result.scalar()
    
    # Revenue by plan
    result = await db.execute(text("""
        SELECT plan, COALESCE(SUM(amount), 0) 
        FROM payments 
        WHERE status = 'paid'
        GROUP BY plan
    """))
    revenue_by_plan = {row[0]: float(row[1]) for row in result.all()}
    
    return {
        "total_revenue": total_revenue,
        "total_payments": total_payments,
        "revenue_30d": revenue_30d,
        "active_subscriptions": active_subs,
        "revenue_by_plan": revenue_by_plan,
    }


async def get_model_metrics(db: AsyncSession) -> Dict[str, Any]:
    """Fetch model performance metrics."""
    # Overall accuracy (last 30 days)
    result = await db.execute(text("""
        SELECT 
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE was_correct = true) as correct,
            ROUND(
                COUNT(*) FILTER (WHERE was_correct = true) * 100.0 / NULLIF(COUNT(*), 0),
                2
            ) as accuracy
        FROM prediction_outcomes
        WHERE resolved_at >= NOW() - INTERVAL '30 days'
    """))
    row = result.first()
    accuracy_stats = {
        "total_predictions": row[0] if row else 0,
        "correct_predictions": row[1] if row else 0,
        "accuracy_pct": float(row[2]) if row and row[2] else 0,
    }
    
    # Accuracy by sport
    result = await db.execute(text("""
        SELECT 
            mp.sport,
            COUNT(*) as total,
            ROUND(
                COUNT(*) FILTER (WHERE po.was_correct = true) * 100.0 / NULLIF(COUNT(*), 0),
                2
            ) as accuracy
        FROM prediction_outcomes po
        JOIN model_predictions mp ON po.prediction_id = mp.id
        WHERE po.resolved_at >= NOW() - INTERVAL '30 days'
        GROUP BY mp.sport
        ORDER BY accuracy DESC
    """))
    by_sport = {row[0]: {"total": row[1], "accuracy": float(row[2]) if row[2] else 0} for row in result.all()}
    
    return {
        "overall": accuracy_stats,
        "by_sport": by_sport,
    }


def print_table(data: Dict[str, Any], title: str):
    """Print data as a formatted table."""
    print(f"\n{'=' * 60}")
    print(f" {title}")
    print(f"{'=' * 60}")
    
    for key, value in data.items():
        if isinstance(value, dict):
            print(f"\n{key}:")
            for k, v in value.items():
                print(f"  {k}: {v}")
        else:
            print(f"{key}: {value}")
    
    print()


def print_json(data: Dict[str, Any]):
    """Print data as JSON."""
    print(json.dumps(data, indent=2, default=str))


async def main():
    parser = argparse.ArgumentParser(description="Run analytics queries")
    parser.add_argument(
        "category",
        nargs="?",
        default="all",
        choices=["users", "usage", "revenue", "model", "all"],
        help="Metrics category to fetch"
    )
    parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="table",
        help="Output format"
    )
    
    args = parser.parse_args()
    
    try:
        db = await get_db_session()
        
        results = {}
        
        if args.category in ("users", "all"):
            results["users"] = await get_user_metrics(db)
        
        if args.category in ("usage", "all"):
            results["usage"] = await get_usage_metrics(db)
        
        if args.category in ("revenue", "all"):
            results["revenue"] = await get_revenue_metrics(db)
        
        if args.category in ("model", "all"):
            results["model"] = await get_model_metrics(db)
        
        await db.close()
        
        if args.format == "json":
            print_json(results)
        else:
            for category, data in results.items():
                print_table(data, category.upper() + " METRICS")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

