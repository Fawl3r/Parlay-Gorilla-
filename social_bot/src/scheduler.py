from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import List, Optional
from urllib.parse import unquote

import pytz
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from src.content_library import ContentLibrary
from src.logging_manager import AuditLogger
from src.models import PostedRecord, QueueItem, parse_iso8601, text_sha256, to_iso8601
from src.publisher import XPublisher
from src.queue_store import QueueStore
from src.settings import Settings, ScheduleSlot
from src.writer import Writer


_REDIRECT_SLUG_RE = re.compile(r"/r/([^\s\?]+)")


class SchedulerService:
    def __init__(
        self,
        *,
        settings: Settings,
        queue_store: QueueStore,
        writer: Writer,
        publisher: XPublisher,
        content: ContentLibrary,
        logger: logging.Logger,
        audit: AuditLogger,
    ) -> None:
        self._settings = settings
        self._queue_store = queue_store
        self._writer = writer
        self._publisher = publisher
        self._content = content
        self._logger = logger
        self._audit = audit
        self._tz = pytz.timezone(settings.bot.timezone)

    def run_blocking(self) -> None:
        scheduler = BlockingScheduler(timezone=self._tz)
        self._register_slots(scheduler, self._settings.scheduler.weekday_schedule, day_of_week="mon-fri", label="weekday")
        self._register_slots(scheduler, self._settings.scheduler.weekend_schedule, day_of_week="sat,sun", label="weekend")
        self._logger.info("Scheduler started")
        scheduler.start()

    def run_slot(self, *, tier: str, label: str, time_str: str) -> None:
        now_utc = datetime.now(timezone.utc)
        now_local = now_utc.astimezone(self._tz)

        posted_raw = self._queue_store.load_posted()
        outbox_items = self._queue_store.hydrate_outbox_items()

        if self._count_posts_today(posted_raw, now_local) >= self._settings.scheduler.max_posts_per_day:
            self._logger.info("Daily cap reached; skipping slot %s %s (%s)", label, time_str, tier)
            return

        item = self._pick_item_for_slot(tier=tier, now_local=now_local, outbox_items=outbox_items, posted_raw=posted_raw)
        if item is None:
            self._logger.info("No eligible items for slot %s %s (%s)", label, time_str, tier)
            return

        self._logger.info("Posting outbox item id=%s type=%s tier=%s", item.id, item.type, tier)
        result = self._publish(item)
        if not result.success:
            self._audit.write("post_failed", {"id": item.id, "error": result.error or "unknown", "pause_until": to_iso8601(result.pause_until) if result.pause_until else None})
            if result.pause_until:
                self._logger.warning("Rate limited; paused until %s", result.pause_until)
            return

        removed = self._queue_store.remove_outbox_item(item.id)
        if removed is None:
            self._logger.warning("Posted item was not present in outbox on disk: %s", item.id)

        record = self._build_posted_record(item=item, tweet_ids=result.tweet_ids, posted_at=now_utc)
        self._queue_store.append_posted(record)
        self._audit.write("posted", {"id": item.id, "tweet_ids": result.tweet_ids, "template_id": item.template_id, "pillar_id": item.pillar_id})

    def _register_slots(self, scheduler: BlockingScheduler, slots: List[ScheduleSlot], *, day_of_week: str, label: str) -> None:
        for slot in slots:
            hour, minute = self._parse_time(slot.time)
            trigger = CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute, timezone=self._tz)
            scheduler.add_job(self.run_slot, trigger=trigger, kwargs={"tier": slot.tier, "label": label, "time_str": slot.time}, max_instances=1)
            self._logger.info("Registered slot %s %s (%s)", label, slot.time, slot.tier)

    def _parse_time(self, value: str) -> tuple[int, int]:
        parts = (value or "").split(":")
        if len(parts) != 2:
            raise ValueError(f"Invalid time: {value}")
        return int(parts[0]), int(parts[1])

    def _publish(self, item: QueueItem):
        if item.type == "single":
            return self._publisher.publish_single(text=item.text or "", image_path=item.image_path)
        return self._publisher.publish_thread(tweets=list(item.tweets or []))

    def _pick_item_for_slot(
        self,
        *,
        tier: str,
        now_local: datetime,
        outbox_items: List[QueueItem],
        posted_raw: List[dict],
    ) -> Optional[QueueItem]:
        # Prefer exact tier first; only fall back when empty.
        candidates = [x for x in outbox_items if x.recommended_tier == tier]
        if not candidates:
            fallback_order = [t for t in self._settings.scheduler.tier_fallback.get(tier, []) if t != tier]
            for fallback_tier in fallback_order:
                candidates = [x for x in outbox_items if x.recommended_tier == fallback_tier]
                if candidates:
                    break
        if not candidates:
            candidates = list(outbox_items)

        candidates = self._avoid_consecutive_pillar(candidates=candidates, posted_raw=posted_raw)
        candidates = self._enforce_thread_weekly_cap(candidates=candidates, posted_raw=posted_raw, now_local=now_local)
        if not candidates:
            return None

        candidates.sort(key=lambda x: (-float(x.score), x.created_at))
        return candidates[0]

    def _avoid_consecutive_pillar(self, *, candidates: List[QueueItem], posted_raw: List[dict]) -> List[QueueItem]:
        last_pillar = ""
        for rec in reversed(posted_raw):
            last_pillar = str(rec.get("pillar_id") or "").strip()
            if last_pillar:
                break
        if not last_pillar:
            return candidates
        filtered = [c for c in candidates if c.pillar_id != last_pillar]
        return filtered or candidates

    def _enforce_thread_weekly_cap(self, *, candidates: List[QueueItem], posted_raw: List[dict], now_local: datetime) -> List[QueueItem]:
        cap = int(self._settings.scheduler.max_threads_per_week)
        if cap <= 0:
            return candidates
        threads_this_week = 0
        now_year, now_week, _ = now_local.isocalendar()
        for rec in posted_raw:
            if str(rec.get("type") or "") != "thread":
                continue
            posted_at = parse_iso8601(str(rec.get("posted_at") or "")).astimezone(self._tz)
            year, week, _ = posted_at.isocalendar()
            if year == now_year and week == now_week:
                threads_this_week += 1
        if threads_this_week < cap:
            return candidates
        return [c for c in candidates if c.type != "thread"]

    def _count_posts_today(self, posted_raw: List[dict], now_local: datetime) -> int:
        today = now_local.date()
        count = 0
        for rec in posted_raw:
            posted_at = parse_iso8601(str(rec.get("posted_at") or "")).astimezone(self._tz)
            if posted_at.date() == today:
                count += 1
        return count

    def _build_posted_record(self, *, item: QueueItem, tweet_ids: List[str], posted_at: datetime) -> PostedRecord:
        template = self._content.templates.get(item.template_id)
        is_disclaimer = bool(getattr(template, "is_disclaimer", False))
        is_analysis = bool(getattr(template, "is_analysis", False))
        analysis_slug = self._extract_slug(item.flattened_text()) if is_analysis else None
        return PostedRecord(
            id=item.id,
            type=item.type,
            posted_at=to_iso8601(posted_at),
            tweet_ids=list(tweet_ids),
            text_hash=text_sha256(item.flattened_text()),
            pillar_id=item.pillar_id,
            template_id=item.template_id,
            score=float(item.score),
            recommended_tier=item.recommended_tier,
            is_disclaimer=is_disclaimer,
            is_analysis=is_analysis,
            analysis_slug=analysis_slug,
            text=(item.text if item.type == "single" else None),
            tweets=(list(item.tweets or []) if item.type == "thread" else None),
        )

    def _extract_slug(self, text: str) -> Optional[str]:
        match = _REDIRECT_SLUG_RE.search(text or "")
        if not match:
            return None
        return unquote(match.group(1)).strip() or None


