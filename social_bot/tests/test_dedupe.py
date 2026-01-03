from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.dedupe import DedupeEngine
from src.models import QueueItem, to_iso8601


def test_dedupe_rejects_similar_outbox_item() -> None:
    engine = DedupeEngine(
        similarity_threshold=0.80,
        template_cooldown_hours=0,
        pillar_cooldown_hours=0,
        recent_window_items=20,
    )
    outbox = [
        QueueItem(
            id="a",
            type="single",
            text="Line shopping matters.",
            pillar_id="p1",
            template_id="t1",
            score=50,
            recommended_tier="mid",
            created_at=to_iso8601(datetime.now(timezone.utc)),
        )
    ]
    candidate = QueueItem(
        id="b",
        type="single",
        text="Line shopping matters!",
        pillar_id="p2",
        template_id="t2",
        score=50,
        recommended_tier="mid",
        created_at=to_iso8601(datetime.now(timezone.utc)),
    )
    decision = engine.check(candidate=candidate, outbox=outbox, posted_raw=[], now=datetime.now(timezone.utc))
    assert decision.ok is False


def test_dedupe_template_cooldown_blocks_recent_template() -> None:
    now = datetime.now(timezone.utc)
    engine = DedupeEngine(
        similarity_threshold=0.99,
        template_cooldown_hours=24,
        pillar_cooldown_hours=0,
        recent_window_items=50,
    )
    posted = [
        {
            "id": "x",
            "type": "single",
            "posted_at": to_iso8601(now - timedelta(hours=1)),
            "tweet_ids": ["1"],
            "text_hash": "h",
            "pillar_id": "p1",
            "template_id": "t1",
            "score": 50,
            "recommended_tier": "mid",
            "is_disclaimer": False,
            "is_analysis": False,
            "analysis_slug": None,
        }
    ]
    candidate = QueueItem(
        id="b",
        type="single",
        text="Different text",
        pillar_id="p2",
        template_id="t1",
        score=50,
        recommended_tier="mid",
        created_at=to_iso8601(now),
    )
    decision = engine.check(candidate=candidate, outbox=[], posted_raw=posted, now=now)
    assert decision.ok is False


