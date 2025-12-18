"""Public bug report endpoint.

This is intentionally lightweight and safe: it captures user-friendly bug reports without
exposing internal implementation details.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_optional_current_user
from app.middleware.rate_limiter import rate_limit
from app.models.user import User
from app.schemas.bug_reports import BugReportCreateRequest, BugReportCreateResponse
from app.services.bug_reports import BugReportService

router = APIRouter()


@router.post("/bug-reports", response_model=BugReportCreateResponse, status_code=201)
@rate_limit("10/hour")
async def create_bug_report(
    request: Request,
    payload: BugReportCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """
    Accept a user-submitted bug report.

    Auth is optional. If the user is signed in, we store user_id for follow-up.
    """
    user_agent = None
    try:
        user_agent = request.headers.get("user-agent")
    except Exception:
        user_agent = None

    service = BugReportService(db)
    created = await service.create_report(payload=payload, user=current_user, user_agent=user_agent)

    return BugReportCreateResponse(id=str(created.id), created_at=service.iso(created.created_at))


