from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, EmailStr, Field


class BugReportCreateRequest(BaseModel):
    title: str = Field(..., min_length=4, max_length=200)
    description: str = Field(..., min_length=10, max_length=4000)
    severity: str = Field("medium", pattern="^(low|medium|high)$")

    # Context
    page_path: Optional[str] = Field(None, max_length=300)
    page_url: Optional[str] = Field(None, max_length=800)
    contact_email: Optional[EmailStr] = None

    # Optional structured details (non-sensitive!)
    steps_to_reproduce: Optional[str] = Field(None, max_length=2000)
    expected_result: Optional[str] = Field(None, max_length=2000)
    actual_result: Optional[str] = Field(None, max_length=2000)

    metadata: Optional[Dict[str, Any]] = None


class BugReportCreateResponse(BaseModel):
    id: str
    created_at: str




