from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy import text

from alembic import context

# Import your models and Base
from app.database.session import Base
from app.models import *  # noqa: F403 -- Import all models for Alembic autogenerate
from app.core.config import settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the database URL from settings (Alembic uses a sync driver)
# Handle SQLite and PostgreSQL URLs
if settings.use_sqlite:
    import os
    sqlite_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "parlay_gorilla.db"
    )
    alembic_db_url = f"sqlite:///{sqlite_path}"
else:
    alembic_db_url = (
        settings.database_url
        .replace("postgresql+asyncpg://", "postgresql://", 1)
        .replace("postgres://", "postgresql://", 1)
    )
config.set_main_option("sqlalchemy.url", alembic_db_url)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# Alembic's default version table column is VARCHAR(32), but this repo uses
# long, descriptive revision IDs (e.g. "011_add_saved_parlays_inscriptions")
# which exceed 32 chars. Ensure the version table can store them.
_ALEMBIC_VERSION_NUM_MAX_LEN = 255


def _ensure_alembic_version_capacity(connection) -> None:
    """
    Ensure `alembic_version.version_num` can store long revision IDs.

    This prevents failures like:
      psycopg2.errors.StringDataRightTruncation: value too long for type character varying(32)
    """
    if connection.dialect.name != "postgresql":
        return

    # 1) Ensure the version table exists with a sufficiently large column.
    # Alembic will reuse an existing table if present.
    connection.execute(
        text(
            f"""
            CREATE TABLE IF NOT EXISTS alembic_version (
              version_num VARCHAR({_ALEMBIC_VERSION_NUM_MAX_LEN}) NOT NULL PRIMARY KEY
            )
            """
        )
    )

    # 2) If an existing install created VARCHAR(32), widen it.
    row = connection.execute(
        text(
            """
            SELECT data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = 'alembic_version'
              AND column_name = 'version_num'
            """
        )
    ).first()

    if not row:
        return

    data_type, max_len = row[0], row[1]
    if data_type == "character varying" and max_len is not None and int(max_len) < _ALEMBIC_VERSION_NUM_MAX_LEN:
        connection.execute(
            text(
                f"ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR({_ALEMBIC_VERSION_NUM_MAX_LEN})"
            )
        )

    # Ensure DDL is persisted before migrations attempt to update the table.
    connection.commit()

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        _ensure_alembic_version_capacity(connection)
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
