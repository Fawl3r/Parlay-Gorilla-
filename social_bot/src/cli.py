from __future__ import annotations

import argparse
import logging
from datetime import datetime, timezone
from random import Random
from typing import List, Optional

from src.content_library import ContentLibrary
from src.dedupe import DedupeEngine
from src.guardian import ComplianceGuardian
from src.logging_manager import AuditLogger, LoggingManager
from src.models import PostedRecord, QueueItem, text_sha256, to_iso8601
from src.publisher import XPublisher
from src.queue_store import QueueStore
from src.scheduler import SchedulerService
from src.settings import SettingsManager
from src.site_feed import SiteFeedClient
from src.writer import Writer


class BotCli:
    def __init__(self) -> None:
        self._parser = argparse.ArgumentParser(prog="social_bot", description="Parlay Gorilla Social Writing Bot")
        sub = self._parser.add_subparsers(dest="command", required=True)

        gen = sub.add_parser("generate", help="Generate posts into queue/outbox.json")
        gen.add_argument("--count", type=int, default=1)

        sub.add_parser("run-scheduler", help="Run APScheduler posting service (blocking)")

        post = sub.add_parser("post-now", help="Post a custom one-off immediately")
        post.add_argument("--text", type=str, required=True)

        thr = sub.add_parser("thread", help="Generate and post a thread immediately")
        thr.add_argument("--topic", type=str, required=True)
        thr.add_argument("--length", type=int, default=5)

    def run(self, argv: Optional[List[str]] = None) -> None:
        args = self._parser.parse_args(argv)
        app = self._build_app()

        if args.command == "generate":
            items = app.writer.generate_and_enqueue(count=args.count)
            app.logger.info("Queued %d item(s).", len(items))
            return

        if args.command == "run-scheduler":
            app.scheduler.run_blocking()
            return

        if args.command == "post-now":
            item = app.writer.build_manual_single(text=args.text)
            self._post_immediately(app, item)
            return

        if args.command == "thread":
            item = app.writer.build_thread(topic=args.topic, length=args.length, rng=Random())
            self._post_immediately(app, item)
            return

        raise SystemExit("Unknown command")

    def _build_app(self) -> "BotApp":
        return _build_app()

    def _post_immediately(self, app: "BotApp", item: QueueItem) -> None:
        posted_raw = app.queue_store.load_posted()
        outbox_items = app.queue_store.hydrate_outbox_items()

        decision = app.dedupe.check(candidate=item, outbox=outbox_items, posted_raw=posted_raw, now=datetime.now(timezone.utc))
        if not decision.ok:
            app.logger.warning("Rejected by dedupe: %s", decision.reason)
            return

        result = app.publisher.publish_thread(tweets=item.tweets or []) if item.type == "thread" else app.publisher.publish_single(text=item.text or "")
        if not result.success:
            app.audit.write("post_failed", {"id": item.id, "error": result.error or "unknown"})
            app.logger.error("Publish failed: %s", result.error)
            return

        record = PostedRecord(
            id=item.id,
            type=item.type,
            posted_at=to_iso8601(datetime.now(timezone.utc)),
            tweet_ids=list(result.tweet_ids),
            text_hash=text_sha256(item.flattened_text()),
            pillar_id=item.pillar_id,
            template_id=item.template_id,
            score=float(item.score),
            recommended_tier=item.recommended_tier,
            is_disclaimer=False,
            is_analysis=False,
            analysis_slug=None,
            text=(item.text if item.type == "single" else None),
            tweets=(list(item.tweets or []) if item.type == "thread" else None),
        )
        app.queue_store.append_posted(record)
        app.audit.write("posted", {"id": item.id, "tweet_ids": result.tweet_ids, "template_id": item.template_id, "pillar_id": item.pillar_id})
        app.logger.info("Posted (dry_run=%s) id=%s tweet_ids=%s", app.settings.bot.dry_run, item.id, result.tweet_ids)


class BotApp:
    def __init__(
        self,
        *,
        settings_manager: SettingsManager,
        content: ContentLibrary,
        guardian: ComplianceGuardian,
        dedupe: DedupeEngine,
        queue_store: QueueStore,
        site_feed: SiteFeedClient,
        writer: Writer,
        publisher: XPublisher,
        scheduler: SchedulerService,
        logger: logging.Logger,
        audit: AuditLogger,
    ) -> None:
        self.settings = settings_manager.load()
        self.content = content
        self.guardian = guardian
        self.dedupe = dedupe
        self.queue_store = queue_store
        self.site_feed = site_feed
        self.writer = writer
        self.publisher = publisher
        self.scheduler = scheduler
        self.logger = logger
        self.audit = audit


def _build_logger_and_audit(project_root, level: str) -> tuple[logging.Logger, AuditLogger]:
    logs_dir = project_root / "logs"
    manager = LoggingManager(logs_dir, level=level)
    return manager.build_logger(), AuditLogger(logs_dir)


def _build_dedupe(settings, disclaimer_template_id: str) -> DedupeEngine:
    return DedupeEngine(
        similarity_threshold=settings.dedupe.similarity_threshold,
        template_cooldown_hours=settings.dedupe.template_cooldown_hours,
        pillar_cooldown_hours=settings.dedupe.pillar_cooldown_hours,
        recent_window_items=settings.dedupe.recent_window_items,
        exempt_template_ids=[disclaimer_template_id],
    )


def _build_site_feed(settings, project_root) -> SiteFeedClient:
    cache_path = project_root / "cache" / "analysis_feed.json"
    return SiteFeedClient(
        analysis_feed_url=settings.site_content.analysis_feed_url,
        cache_path=cache_path,
        cache_ttl_seconds=settings.site_content.analysis_feed_cache_ttl_seconds,
        slug_reuse_cooldown_hours=settings.site_content.slug_reuse_cooldown_hours,
        redirect_base_url=settings.site_content.redirect_base_url,
        ab_variants=settings.site_content.ab_variants,
        timeout_seconds=settings.publisher.timeout_seconds,
    )


def _build_publisher(settings) -> XPublisher:
    return XPublisher(
        api_base_url=settings.publisher.api_base_url,
        bearer_token=settings.publisher.bearer_token,
        dry_run=settings.bot.dry_run,
        max_retries=settings.publisher.max_retries,
        backoff_initial_seconds=settings.publisher.backoff_initial_seconds,
        backoff_max_seconds=settings.publisher.backoff_max_seconds,
        timeout_seconds=settings.publisher.timeout_seconds,
    )


def _build_guardian(settings, banned_phrases: List[str]) -> ComplianceGuardian:
    return ComplianceGuardian(
        banned_phrases=banned_phrases,
        max_length=settings.guardian.max_length,
        max_hashtags=settings.guardian.max_hashtags,
        max_emojis=settings.guardian.max_emojis,
        banned_phrase_action=settings.guardian.banned_phrase_action,
    )


def _build_scheduler(*, settings, queue_store, writer, publisher, content, logger, audit) -> SchedulerService:
    return SchedulerService(
        settings=settings,
        queue_store=queue_store,
        writer=writer,
        publisher=publisher,
        content=content,
        logger=logger,
        audit=audit,
    )


def _build_writer(*, settings, content, guardian, dedupe, queue_store, site_feed, audit) -> Writer:
    return Writer(
        settings=settings,
        content=content,
        guardian=guardian,
        dedupe=dedupe,
        queue_store=queue_store,
        site_feed=site_feed,
        audit=audit,
    )


def _build_queue_store(project_root) -> QueueStore:
    return QueueStore(project_root / "queue")


def _load_content(project_root) -> ContentLibrary:
    return ContentLibrary(project_root / "content").load()


def _load_settings_manager() -> SettingsManager:
    return SettingsManager()


def _load_settings(settings_manager: SettingsManager):
    return settings_manager.load()


def _build_app_dependencies() -> tuple[SettingsManager, "BotApp"]:
    sm = _load_settings_manager()
    settings = _load_settings(sm)

    logger, audit = _build_logger_and_audit(sm.project_root, settings.bot.log_level)
    content = _load_content(sm.project_root)
    guardian = _build_guardian(settings, content.banned_phrases)
    dedupe = _build_dedupe(settings, settings.scheduler.disclaimer_template_id)
    queue_store = _build_queue_store(sm.project_root)
    site_feed = _build_site_feed(settings, sm.project_root)
    writer = _build_writer(settings=settings, content=content, guardian=guardian, dedupe=dedupe, queue_store=queue_store, site_feed=site_feed, audit=audit)
    publisher = _build_publisher(settings)
    scheduler = _build_scheduler(settings=settings, queue_store=queue_store, writer=writer, publisher=publisher, content=content, logger=logger, audit=audit)
    return sm, BotApp(
        settings_manager=sm,
        content=content,
        guardian=guardian,
        dedupe=dedupe,
        queue_store=queue_store,
        site_feed=site_feed,
        writer=writer,
        publisher=publisher,
        scheduler=scheduler,
        logger=logger,
        audit=audit,
    )


def _build_app() -> "BotApp":
    _, app = _build_app_dependencies()
    return app
