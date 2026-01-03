from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from random import Random
from typing import List, Optional, Tuple
from uuid import uuid4

from src.content_library import ContentLibrary, PillarDefinition, TemplateDefinition
from src.dynamic_context import DynamicContextBuilder
from src.dedupe import DedupeEngine
from src.guardian import ComplianceGuardian, GuardianRejectError
from src.logging_manager import AuditLogger
from src.images import ImagePipeline
from src.models import QueueItem, to_iso8601, utc_now
from src.queue_store import QueueStore
from src.site_feed import SiteFeedClient
from src.settings import Settings


class Writer:
    def __init__(
        self,
        *,
        settings: Settings,
        content: ContentLibrary,
        guardian: ComplianceGuardian,
        dedupe: DedupeEngine,
        queue_store: QueueStore,
        site_feed: SiteFeedClient,
        dynamic_context: DynamicContextBuilder,
        audit: AuditLogger,
        image_pipeline: Optional[ImagePipeline] = None,
    ) -> None:
        self._settings = settings
        self._content = content
        self._guardian = guardian
        self._dedupe = dedupe
        self._queue_store = queue_store
        self._site_feed = site_feed
        self._dynamic_context = dynamic_context
        self._audit = audit
        self._image_pipeline = image_pipeline

    def generate_and_enqueue(
        self,
        *,
        count: int,
        rng: Optional[Random] = None,
        now: Optional[datetime] = None,
    ) -> List[QueueItem]:
        rng = rng or Random()
        now = now or utc_now()
        posted_raw = self._queue_store.load_posted()
        outbox_items = self._queue_store.hydrate_outbox_items()

        created: List[QueueItem] = []
        to_append: List[dict] = []
        for _ in range(int(count)):
            item = self._generate_with_retries(rng=rng, now=now, outbox=outbox_items, posted_raw=posted_raw)
            if item is None:
                continue
            created.append(item)
            outbox_items.append(item)
            to_append.append(item.to_outbox_dict())
            self._audit.write("queued", {"id": item.id, "type": item.type, "pillar_id": item.pillar_id, "template_id": item.template_id})

        if to_append:
            self._queue_store.append_outbox(to_append)
        return created

    def build_manual_single(self, *, text: str) -> QueueItem:
        cleaned = self._guardian.enforce_single(text)
        score = 50.0
        return QueueItem(
            id=str(uuid4()),
            type="single",
            text=cleaned,
            pillar_id="manual",
            template_id="manual",
            score=score,
            recommended_tier=self._tier_for_score(score),
            created_at=to_iso8601(utc_now()),
        )

    def build_thread(self, *, topic: str, length: int, rng: Optional[Random] = None) -> QueueItem:
        rng = rng or Random()
        length = int(length)
        if length < 3 or length > 6:
            raise ValueError("Thread length must be between 3 and 6")
        topic_clean = " ".join((topic or "").strip().split())
        if not topic_clean:
            raise ValueError("Topic is required")

        tweets = self._generate_thread_tweets(topic=topic_clean, length=length, rng=rng)
        enforced = self._guardian.enforce_thread(tweets)
        score = 75.0
        return QueueItem(
            id=str(uuid4()),
            type="thread",
            tweets=enforced,
            topic=topic_clean,
            pillar_id="betting_discipline",
            template_id="thread_manual",
            score=score,
            recommended_tier=self._tier_for_score(score),
            created_at=to_iso8601(utc_now()),
        )

    def _generate_with_retries(
        self,
        *,
        rng: Random,
        now: datetime,
        outbox: List[QueueItem],
        posted_raw: List[dict],
    ) -> Optional[QueueItem]:
        for _ in range(int(self._settings.writer.max_generate_attempts_per_item)):
            try:
                item = self._generate_one(rng=rng, now=now, outbox=outbox, posted_raw=posted_raw)
                item = self._enforce(item)
                decision = self._dedupe.check(candidate=item, outbox=outbox, posted_raw=posted_raw, now=now)
                if decision.ok:
                    item = self._maybe_attach_image(item=item, rng=rng, now=now)
                    return item
            except GuardianRejectError:
                continue
            except Exception:
                continue
        return None

    def _maybe_attach_image(self, *, item: QueueItem, rng: Random, now: datetime) -> QueueItem:
        if not self._image_pipeline:
            return item
        if item.type != "single":
            return item
        try:
            attachment = self._image_pipeline.maybe_generate(
                post_id=item.id,
                post_text=item.text or "",
                pillar_id=item.pillar_id,
                template_id=item.template_id,
                rng=rng,
                now=now,
            )
            if attachment is None:
                return item
            return replace(item, image_mode=attachment.image_mode, image_path=attachment.image_path)
        except Exception as exc:
            self._audit.write("image_failed", {"id": item.id, "error": str(exc)[:200]})
            return item

    def _generate_one(self, *, rng: Random, now: datetime, outbox: List[QueueItem], posted_raw: List[dict]) -> QueueItem:
        pillar = self._content.choose_pillar(rng, now)

        if pillar.id == "analysis_excerpts" and rng.random() < self._settings.writer.analysis_injection_probability:
            analysis_item = self._site_feed.get_injectable_item(now=now, posted_raw=posted_raw)
            if analysis_item:
                return self._build_analysis_post(pillar=pillar, rng=rng, now=now, analysis=analysis_item)

        template = self._choose_template_for_pillar(pillar=pillar, rng=rng, allow_analysis=False)
        tokens = self._dynamic_context.build(rng=rng, now=now, posted_raw=posted_raw)
        hook_text = self._maybe_pick_hook_text(rng=rng, outbox=outbox, posted_raw=posted_raw)
        text = self._render_template(template, tokens)
        if hook_text:
            text = f"{hook_text}\n\n{text}"

        score = float(template.base_score) + rng.uniform(-6.0, 6.0)
        score = max(0.0, min(100.0, score))
        return QueueItem(
            id=str(uuid4()),
            type="single",
            text=text,
            pillar_id=pillar.id,
            template_id=template.id,
            score=score,
            recommended_tier=self._tier_for_score(score),
            created_at=to_iso8601(utc_now()),
        )

    def _build_analysis_post(
        self,
        *,
        pillar: PillarDefinition,
        rng: Random,
        now: datetime,
        analysis: Tuple,
    ) -> QueueItem:
        item, variant = analysis
        template_id = "analysis_risk_note" if item.risk_note else "analysis_matchup_angle"
        template = self._content.get_template(template_id)

        key_points = item.key_points[:3] if item.key_points else []
        kp1 = key_points[0] if len(key_points) > 0 else "Matchup context matters more than vibes."
        kp2 = key_points[1] if len(key_points) > 1 else "Price discipline beats hot takes over time."

        url = self._site_feed.build_tracking_url(slug=item.slug, variant=variant)
        text = template.text.format(
            angle=item.angle[:220].strip(),
            kp1=kp1[:120].strip(),
            kp2=kp2[:120].strip(),
            risk_note=(item.risk_note or "")[:140].strip(),
            url=url,
        )

        score = float(template.base_score) + rng.uniform(-4.0, 6.0)
        score = max(0.0, min(100.0, score))
        return QueueItem(
            id=str(uuid4()),
            type="single",
            text=text,
            pillar_id=pillar.id,
            template_id=template.id,
            score=score,
            recommended_tier=self._tier_for_score(score),
            created_at=to_iso8601(utc_now()),
        )

    def _choose_template_for_pillar(self, *, pillar: PillarDefinition, rng: Random, allow_analysis: bool) -> TemplateDefinition:
        suggested = list(pillar.suggested_templates or [])
        if suggested and rng.random() < self._settings.writer.suggested_template_bias:
            chosen = self._content.get_template(rng.choice(suggested))
            if allow_analysis or not chosen.is_analysis:
                if not chosen.is_disclaimer:
                    return chosen

        candidates = [
            t for t in self._content.templates.values()
            if t.type == "single"
            and (allow_analysis or not t.is_analysis)
            and not t.is_disclaimer
        ]
        if not candidates:
            raise ValueError("No eligible templates available (all are disclaimers or analysis-only)")
        return rng.choice(candidates)

    def _render_template(self, template: TemplateDefinition, tokens: dict) -> str:
        class _SafeDict(dict):
            def __missing__(self, key: str) -> str:  # type: ignore[override]
                return ""

        try:
            rendered = template.text.format_map(_SafeDict(tokens)).strip()
        except Exception:
            rendered = (template.text or "").strip()
        return rendered

    def _maybe_pick_hook_text(self, *, rng: Random, outbox: List[QueueItem], posted_raw: List[dict]) -> Optional[str]:
        if rng.random() >= float(self._settings.writer.hook_probability):
            return None
        excluded: List[str] = []
        for _ in range(6):
            hook = self._content.choose_hook(rng, exclude_texts=excluded)
            if hook is None:
                return None
            if not self._dedupe.is_hook_recently_used(hook.text, outbox=outbox, posted_raw=posted_raw):
                return hook.text
            excluded.append(hook.text)
        return None

    def _enforce(self, item: QueueItem) -> QueueItem:
        if item.type == "single":
            enforced = self._guardian.enforce_single(item.text or "")
            return replace(item, text=enforced)
        enforced_tweets = self._guardian.enforce_thread(item.tweets or [])
        return replace(item, tweets=enforced_tweets)

    def _tier_for_score(self, score: float) -> str:
        if score >= 80:
            return "high"
        if score >= 55:
            return "mid"
        return "low"

    def _generate_thread_tweets(self, *, topic: str, length: int, rng: Random) -> List[str]:
        base_points = [
            "Define your thesis first (why this bet makes sense).",
            "Shop lines. A half-point is real money over time.",
            "Avoid staking changes driven by emotion.",
            "If you can’t explain the edge, you don’t have one.",
            "Track results by market + price, not by vibes.",
            "Quit chasing. The next bet isn’t owed to you."
        ]
        rng.shuffle(base_points)
        points = base_points[: max(1, length - 2)]
        tweets: List[str] = [f"1/{length} {topic} — quick thread."]
        for idx, point in enumerate(points, start=2):
            tweets.append(f"{idx}/{length} {point}")
        tweets.append(f"{length}/{length} Bet responsibly. Long run > short run.")
        return tweets[:length]


