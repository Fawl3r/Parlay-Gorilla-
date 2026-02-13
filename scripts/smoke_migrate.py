#!/usr/bin/env python3
"""
Smoke test: run migrate_with_lock when DATABASE_URL points at Postgres.
Usage: from repo root, with DATABASE_URL set and DB reachable:
  python scripts/smoke_migrate.py
  cd backend && python -m app.ops.migrate_with_lock   # equivalent
Exits 0 if migrations ran (or already at head), non-zero on failure.
"""

from __future__ import annotations

import os
import subprocess
import sys


def main() -> int:
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    backend = os.path.join(repo_root, "backend")
    if not os.path.isdir(backend):
        print("backend/ not found", file=sys.stderr)
        return 1
    code = subprocess.run(
        [sys.executable, "-m", "app.ops.migrate_with_lock"],
        cwd=backend,
        env=os.environ.copy(),
    ).returncode
    return code


if __name__ == "__main__":
    sys.exit(main())
