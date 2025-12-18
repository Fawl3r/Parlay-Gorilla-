from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bug_report import BugReport


class BugReportRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def add(self, report: BugReport) -> BugReport:
        self._db.add(report)
        await self._db.flush()
        return report




