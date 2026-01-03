from __future__ import annotations

from datetime import datetime, timezone
from random import Random

from src.content_library import ContentLibrary
from src.dedupe import DedupeEngine
from src.guardian import ComplianceGuardian
from src.logging_manager import AuditLogger
from src.queue_store import QueueStore
from src.settings import SettingsManager
from src.site_feed import SiteFeedClient
from src.writer import Writer


def test_writer_determinism_under_seeded_rng(bot_project_root) -> None:
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
        analysis_feed_url=settings.site_content.analysis_feed_url,
        cache_path=bot_project_root / "cache" / "analysis_feed.json",
        cache_ttl_seconds=settings.site_content.analysis_feed_cache_ttl_seconds,
        slug_reuse_cooldown_hours=settings.site_content.slug_reuse_cooldown_hours,
        redirect_base_url=settings.site_content.redirect_base_url,
        ab_variants=settings.site_content.ab_variants,
        timeout_seconds=settings.publisher.timeout_seconds,
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

    fixed_now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    queue_store.save_outbox([])
    items_a = writer.generate_and_enqueue(count=5, rng=Random(123), now=fixed_now)
    sig_a = [(i.template_id, i.text) for i in items_a]

    queue_store.save_outbox([])
    items_b = writer.generate_and_enqueue(count=5, rng=Random(123), now=fixed_now)
    sig_b = [(i.template_id, i.text) for i in items_b]

    assert sig_a == sig_b


