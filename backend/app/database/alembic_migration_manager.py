from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.util.exc import CommandError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AlembicMigrationPaths:
    backend_dir: Path

    @property
    def alembic_ini_path(self) -> Path:
        return self.backend_dir / "alembic.ini"

    @property
    def alembic_script_location(self) -> Path:
        return self.backend_dir / "alembic"


class AlembicMigrationManager:
    """
    Runs Alembic migrations programmatically.

    Why this exists:
    - In production, relying on SQLAlchemy `create_all()` causes schema drift because it does not add columns.
    - When drift happens, core endpoints like auth can start returning 500s (UndefinedColumnError).
    """

    def __init__(self) -> None:
        backend_dir = Path(__file__).resolve().parents[2]
        self._paths = AlembicMigrationPaths(backend_dir=backend_dir)

    def _build_config(self) -> Config:
        cfg = Config(str(self._paths.alembic_ini_path))

        # Ensure we can run from any working directory (e.g. Render) by making
        # script_location absolute.
        cfg.set_main_option("script_location", str(self._paths.alembic_script_location))

        # Alembic env.py sets sqlalchemy.url from app settings.
        return cfg

    def upgrade_head(self) -> None:
        """Upgrade database to head revision with error handling."""
        cfg = self._build_config()
        try:
            command.upgrade(cfg, "head")
            logger.info("Database migrations completed successfully")
        except CommandError as e:
            logger.error(f"Migration failed: {e}")
            # Re-raise to allow caller to handle
            raise
        except Exception as e:
            logger.error(f"Unexpected error during migration: {e}", exc_info=True)
            raise

    async def upgrade_head_async(self) -> None:
        """Upgrade database to head revision asynchronously with error handling."""
        # Alembic runs synchronously; run it off the event loop.
        try:
            await asyncio.to_thread(self.upgrade_head)
        except Exception as e:
            logger.error(f"Async migration failed: {e}", exc_info=True)
            # Don't re-raise - let the application continue
            # The startup event handler will log the error and continue
            pass


