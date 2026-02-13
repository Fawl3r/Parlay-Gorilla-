"""Unit and lightweight integration tests for app.ops.migrate_with_lock."""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

# Import helpers and constants without running main (so we can test under patched env).
from app.ops.migrate_with_lock import (
    LOCK_KEY,
    _backend_root,
    _get_sync_postgres_url,
)


class TestGetSyncPostgresUrl:
    """Test URL normalization and validation."""

    def test_converts_asyncpg_to_postgresql(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@host/db")
        assert _get_sync_postgres_url() == "postgresql://u:p@host/db"

    def test_converts_postgres_to_postgresql(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DATABASE_URL", "postgres://u:p@host/db")
        assert _get_sync_postgres_url() == "postgresql://u:p@host/db"

    def test_leaves_postgresql_unchanged(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@host/db")
        assert _get_sync_postgres_url() == "postgresql://u:p@host/db"

    def test_raises_when_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("DATABASE_URL", raising=False)
        with pytest.raises(ValueError, match="DATABASE_URL is required"):
            _get_sync_postgres_url()

    def test_raises_for_sqlite(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///foo.db")
        with pytest.raises(ValueError, match="PostgreSQL"):
            _get_sync_postgres_url()


class TestLockKey:
    """Lock key is a fixed int64 for advisory lock."""

    def test_lock_key_constant(self) -> None:
        assert LOCK_KEY == 987654321
        assert isinstance(LOCK_KEY, int)


class TestBackendRoot:
    """Backend root resolves to directory containing alembic.ini."""

    def test_backend_root_contains_alembic_ini(self) -> None:
        root = _backend_root()
        assert os.path.isdir(root)
        assert os.path.isfile(os.path.join(root, "alembic.ini"))


class TestMainExitCodes:
    """Smoke: main() exit codes without a real DB."""

    def test_main_exits_nonzero_when_database_url_missing(self) -> None:
        """Running migrate_with_lock with no DATABASE_URL should exit 1."""
        result = subprocess.run(
            [sys.executable, "-m", "app.ops.migrate_with_lock"],
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            env={k: v for k, v in os.environ.items() if k != "DATABASE_URL"},
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode != 0
        assert "DATABASE_URL" in (result.stderr or result.stdout or "")

    def test_main_exits_nonzero_for_sqlite_url(self) -> None:
        """Running with SQLite DATABASE_URL should exit 1 (lock requires Postgres)."""
        result = subprocess.run(
            [sys.executable, "-m", "app.ops.migrate_with_lock"],
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            env={**os.environ, "DATABASE_URL": "sqlite+aiosqlite:///x.db"},
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode != 0
        assert "PostgreSQL" in (result.stderr or result.stdout or "")
