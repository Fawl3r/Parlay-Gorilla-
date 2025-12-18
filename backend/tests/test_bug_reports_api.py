from __future__ import annotations

import pytest
from sqlalchemy import select, func

from app.models.bug_report import BugReport


@pytest.mark.asyncio
async def test_create_bug_report_anonymous(client, db):
    payload = {
        "title": "Game analysis page shows wrong odds",
        "description": "On the analysis page, the spread/total looks incorrect for one matchup.",
        "severity": "medium",
        "page_path": "/analysis/nfl/some-game",
        "page_url": "https://example.com/analysis/nfl/some-game",
        "contact_email": "user@example.com",
        "steps_to_reproduce": "Open the analysis page and compare to sportsbook.",
        "expected_result": "The odds match the latest market.",
        "actual_result": "The odds are different than expected.",
        "metadata": {"ui": "analysis", "browser": "test"},
    }

    res = await client.post("/api/bug-reports", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert "id" in data and data["id"]
    assert "created_at" in data and data["created_at"]

    count_res = await db.execute(select(func.count()).select_from(BugReport))
    assert int(count_res.scalar_one() or 0) == 1


@pytest.mark.asyncio
async def test_create_bug_report_validates_required_fields(client):
    # Missing description
    res = await client.post("/api/bug-reports", json={"title": "Too short", "severity": "low"})
    assert res.status_code in (400, 422)




