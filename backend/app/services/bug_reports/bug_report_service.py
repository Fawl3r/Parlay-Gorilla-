from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bug_report import BugReport
from app.models.user import User
from app.schemas.bug_reports import BugReportCreateRequest
from app.services.bug_reports.bug_report_repository import BugReportRepository


class BugReportService:
    def __init__(self, db: AsyncSession):
        self._db = db
        self._repo = BugReportRepository(db)

    async def create_report(
        self,
        *,
        payload: BugReportCreateRequest,
        user: Optional[User],
        user_agent: Optional[str],
    ) -> BugReport:
        metadata: Dict[str, Any] = dict(payload.metadata or {})

        # Attach optional text fields in metadata so the core table stays compact.
        if payload.steps_to_reproduce:
            metadata["steps_to_reproduce"] = payload.steps_to_reproduce
        if payload.expected_result:
            metadata["expected_result"] = payload.expected_result
        if payload.actual_result:
            metadata["actual_result"] = payload.actual_result

        report = BugReport(
            user_id=getattr(user, "id", None),
            contact_email=str(payload.contact_email) if payload.contact_email else None,
            title=payload.title.strip(),
            description=payload.description.strip(),
            severity=str(payload.severity or "medium").strip().lower(),
            page_path=(payload.page_path or "").strip() or None,
            page_url=(payload.page_url or "").strip() or None,
            user_agent=(user_agent or "").strip() or None,
            metadata_=metadata or None,
        )

        created = await self._repo.add(report)
        await self._db.commit()
        # Ensure created_at is available in response (SQLite might not refresh automatically).
        await self._db.refresh(created)
        return created

    @staticmethod
    def iso(dt: Optional[datetime]) -> str:
        value = dt or datetime.now(tz=timezone.utc)
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()




