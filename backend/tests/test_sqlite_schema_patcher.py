import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


@pytest.mark.asyncio
async def test_sqlite_schema_patcher_adds_premium_ai_columns(tmp_path):
    """
    Regression test:
    Old dev SQLite DBs can miss `users.premium_ai_parlays_used`, which crashes auth
    (SQLAlchemy selects all User columns).
    """
    db_path = tmp_path / "schema-test.sqlite"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path.as_posix()}")

    async with engine.begin() as conn:
        # Simulate an older schema missing the premium_ai_parlays_* columns.
        await conn.execute(
            text(
                """
                CREATE TABLE users (
                    id VARCHAR(36) PRIMARY KEY,
                    email VARCHAR
                )
                """
            )
        )

        from app.database.sqlite_schema_patcher import SqliteSchemaPatcher

        patcher = SqliteSchemaPatcher(conn)
        await patcher.ensure_dev_schema()

        result = await conn.execute(text("PRAGMA table_info(users)"))
        columns = {row[1] for row in result}

        assert "premium_ai_parlays_used" in columns
        assert "premium_ai_parlays_period_start" in columns

        # Ensure the added column is queryable.
        await conn.execute(text("SELECT premium_ai_parlays_used FROM users LIMIT 1"))

    await engine.dispose()


