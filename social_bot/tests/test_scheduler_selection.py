from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from src.content_library import ContentLibrary
from src.logging_manager import AuditLogger
from src.publisher import XPublisher
from src.queue_store import QueueStore
from src.scheduler import SchedulerService
from src.settings import SettingsManager
from src.site_feed import SiteFeedClient
from src.dedupe import DedupeEngine
from src.guardian import ComplianceGuardian
from src.writer import Writer
from src.models import QueueItem, to_iso8601


def test_scheduler_selects_tier_and_avoids_pillar_repeat(bot_project_root) -> None:
    # Disable disclaimer forcing for this routing test.
    cfg_path = bot_project_root / "config" / "settings.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    cfg["scheduler"]["ensure_disclaimer_once_per_day"] = False
    cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

    sm = SettingsManager(project_root=bot_project_root)
    settings = sm.load()
    content = ContentLibrary(bot_project_root / "content").load()
    queue_store = QueueStore(bot_project_root / "queue")
    audit = AuditLogger(bot_project_root / "logs")

    guardian = ComplianceGuardian(
        banned_phrases=content.banned_phrases,
        max_length=settings.guardian.max_length,
        max_hashtags=settings.guardian.max_hashtags,
        max_emojis=settings.guardian.max_emojis,
        banned_phrase_action=settings.guardian.banned_phrase_action,
    )
    dedupe = DedupeEngine(
        similarity_threshold=settings.dedupe.similarity_threshold,
        template_cooldown_hours=settings.dedupe.template_cooldown_hours,
        pillar_cooldown_hours=settings.dedupe.pillar_cooldown_hours,
        recent_window_items=settings.dedupe.recent_window_items,
        exempt_template_ids=[settings.scheduler.disclaimer_template_id],
    )
    site_feed = SiteFeedClient(
        analysis_feed_url="",
        cache_path=bot_project_root / "cache" / "analysis_feed.json",
        cache_ttl_seconds=3600,
        slug_reuse_cooldown_hours=48,
        redirect_base_url="http://localhost:8000",
        ab_variants=["a", "b"],
        timeout_seconds=1.0,
    )
    writer = Writer(
        settings=settings,
        content=content,
        guardian=guardian,
        dedupe=dedupe,
        queue_store=queue_store,
        site_feed=site_feed,
        audit=audit,
    )
    publisher = XPublisher(
        api_base_url=settings.publisher.api_base_url,
        bearer_token="",
        dry_run=True,
        max_retries=0,
        backoff_initial_seconds=0.0,
        backoff_max_seconds=0.0,
        timeout_seconds=1.0,
    )
    logger = logging.getLogger("scheduler_test")
    logger.addHandler(logging.NullHandler())

    scheduler = SchedulerService(
        settings=settings,
        queue_store=queue_store,
        writer=writer,
        publisher=publisher,
        content=content,
        logger=logger,
        audit=audit,
    )

    now_local = datetime.now(timezone.utc)
    outbox_items = [
        QueueItem(id="1", type="single", text="A", pillar_id="p1", template_id="t1", score=90, recommended_tier="mid", created_at=to_iso8601(now_local)),
        QueueItem(id="2", type="single", text="B", pillar_id="p2", template_id="t2", score=80, recommended_tier="mid", created_at=to_iso8601(now_local)),
        QueueItem(id="3", type="single", text="C", pillar_id="p3", template_id="t2", score=95, recommended_tier="low", created_at=to_iso8601(now_local)),
    ]

    picked = scheduler._pick_item_for_slot(tier="mid", now_local=now_local, outbox_items=outbox_items, posted_raw=[])
    assert picked is not None
    assert picked.id == "1"

    posted_raw = [{"posted_at": to_iso8601(now_local), "pillar_id": "p1", "type": "single"}]
    picked2 = scheduler._pick_item_for_slot(tier="mid", now_local=now_local, outbox_items=outbox_items, posted_raw=posted_raw)
    assert picked2 is not None
    assert picked2.id == "2"


