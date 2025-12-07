"""Test database connection and check tables/data"""
import asyncio
from sqlalchemy import text

async def test_db():
    try:
        from app.database.session import engine
        async with engine.connect() as conn:
            result = await conn.execute(text('SELECT 1'))
            print('Database connection: SUCCESS')
            
            # Check tables
            result = await conn.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            print(f'Tables found: {len(tables)}')
            for t in tables:
                print(f'  - {t}')
            
            # Check games count
            if 'games' in tables:
                result = await conn.execute(text('SELECT COUNT(*) FROM games'))
                count = result.scalar()
                print(f'\nGames count: {count}')
                
                if count > 0:
                    result = await conn.execute(text("""
                        SELECT id, sport, home_team, away_team, start_time, status 
                        FROM games ORDER BY start_time DESC LIMIT 5
                    """))
                    print('Recent games:')
                    for row in result.fetchall():
                        print(f'  {row[2]} vs {row[3]} ({row[1]}) - {row[5]}')
            else:
                print('\nGames table does not exist!')
                
            # Check odds count
            if 'odds' in tables:
                result = await conn.execute(text('SELECT COUNT(*) FROM odds'))
                count = result.scalar()
                print(f'\nOdds count: {count}')
            
            # Check markets count  
            if 'markets' in tables:
                result = await conn.execute(text('SELECT COUNT(*) FROM markets'))
                count = result.scalar()
                print(f'Markets count: {count}')
                
    except Exception as e:
        print(f'Database connection: FAILED - {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_db())
