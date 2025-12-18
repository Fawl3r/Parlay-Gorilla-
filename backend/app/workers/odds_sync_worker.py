"""Odds sync worker for keeping odds up to date"""

import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import AsyncSessionLocal
from app.services.odds_fetcher import OddsFetcherService
from app.services.sports_config import list_supported_sports, get_sport_config
from app.services.odds_history.odds_history_sync_service import OddsHistorySyncService


class OddsSyncWorker:
    """Background worker for syncing odds from The Odds API"""
    
    async def sync_all_sports(self):
        """Sync odds for all supported sports"""
        sports = list_supported_sports()
        
        async with AsyncSessionLocal() as db:
            fetcher = OddsFetcherService(db)
            history_sync = OddsHistorySyncService(db)
            
            for sport_config in sports:
                try:
                    print(f"[ODDS_SYNC_WORKER] Syncing odds for {sport_config.slug}...")
                    
                    # Fetch fresh odds
                    api_data = await fetcher.fetch_odds_for_sport(sport_config)
                    
                    if api_data:
                        # Store in database
                        games = await fetcher.normalize_and_store_odds(api_data, sport_config)
                        await db.commit()
                        print(f"[ODDS_SYNC_WORKER] Synced {len(games)} games for {sport_config.slug}")
                    else:
                        print(f"[ODDS_SYNC_WORKER] No games found for {sport_config.slug}")

                    # Once per day per sport: store a lookback snapshot for line movement.
                    try:
                        stored = await history_sync.sync_daily_lookback_24h_for_sport(sport_config=sport_config)
                        if stored:
                            print(f"[ODDS_SYNC_WORKER] Stored {stored} historical snapshots for {sport_config.slug}")
                    except Exception as hist_exc:
                        print(f"[ODDS_SYNC_WORKER] Historical odds sync skipped for {sport_config.slug}: {hist_exc}")
                        
                except Exception as e:
                    print(f"[ODDS_SYNC_WORKER] Error syncing {sport_config.slug}: {e}")
                    await db.rollback()
                    continue
    
    async def sync_single_sport(self, sport: str):
        """Sync odds for a single sport"""
        async with AsyncSessionLocal() as db:
            try:
                fetcher = OddsFetcherService(db)
                sport_config = get_sport_config(sport)
                
                api_data = await fetcher.fetch_odds_for_sport(sport_config)
                
                if api_data:
                    games = await fetcher.normalize_and_store_odds(api_data, sport_config)
                    await db.commit()
                    return len(games)
                return 0
            except Exception as e:
                print(f"[ODDS_SYNC_WORKER] Error syncing {sport}: {e}")
                await db.rollback()
                return 0


async def run_odds_sync_worker():
    """Main entry point for odds sync worker"""
    worker = OddsSyncWorker()
    await worker.sync_all_sports()


if __name__ == "__main__":
    asyncio.run(run_odds_sync_worker())

