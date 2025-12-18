import asyncio
from sqlalchemy import select

from app.database.session import AsyncSessionLocal
from app.models.game import Game


async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Game).where(
                Game.home_team.ilike("%Buccaneers%"),
                Game.away_team.ilike("%Falcons%"),
            )
        )
        games = result.scalars().all()
        for g in games:
            print(g.id, g.home_team, g.away_team, g.start_time)


if __name__ == "__main__":
    asyncio.run(main())

