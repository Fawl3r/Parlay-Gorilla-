"""Check for case-insensitive duplicate emails in the users table.

Usage:
  python backend/scripts/check_case_insensitive_email_duplicates.py

Exits non-zero if duplicates exist.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
import sys

from sqlalchemy import text

_BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.database.session import engine


class CaseInsensitiveEmailDuplicateChecker:
    async def find_duplicates(self) -> list[tuple[str, int]]:
        async with engine.begin() as conn:
            result = await conn.execute(
                text(
                    """
                    SELECT lower(email) AS email_norm, COUNT(*) AS cnt
                    FROM users
                    GROUP BY lower(email)
                    HAVING COUNT(*) > 1
                    ORDER BY cnt DESC, email_norm ASC
                    """
                )
            )
            return [(str(r[0]), int(r[1])) for r in result.fetchall()]


async def _main_async() -> int:
    checker = CaseInsensitiveEmailDuplicateChecker()
    duplicates = await checker.find_duplicates()

    if not duplicates:
        print("OK: no case-insensitive duplicate emails found.")
        return 0

    print("ERROR: case-insensitive duplicate emails found:")
    for email_norm, cnt in duplicates:
        print(f" - {email_norm}: {cnt}")
    return 1


def main() -> None:
    try:
        code = asyncio.run(_main_async())
    except KeyboardInterrupt:
        code = 130
    sys.exit(code)


if __name__ == "__main__":
    main()


