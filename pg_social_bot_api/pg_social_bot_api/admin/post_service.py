from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from pg_social_bot_api.admin.audit_logger import AuditLogger
from pg_social_bot_api.admin.banned_phrases import BannedPhrasesService
from pg_social_bot_api.admin.post_repository import PostRepository
from pg_social_bot_api.core.config import get_settings
from pg_social_bot_api.images.post_image_generator import ImageGenerationError, PostImageGenerator
from pg_social_bot_api.models.enums import PostStatus
from pg_social_bot_api.models.post import Post


@dataclass(frozen=True)
class ComplianceError:
    matched_phrases: list[str]


class PostService:
    def __init__(self) -> None:
        self._repo = PostRepository()
        self._audit = AuditLogger()
        self._banned = BannedPhrasesService()

    async def create_draft(
        self,
        db: AsyncSession,
        *,
        actor_user_id: uuid.UUID,
        text: str,
        pillar_id: str,
        template_id: str,
        mode_id: str,
        tier: str,
        cta_url: Optional[str],
        analysis_slug: Optional[str],
    ) -> Post:
        post = Post(
            status=PostStatus.draft.value,
            text=text,
            pillar_id=pillar_id,
            template_id=template_id,
            mode_id=mode_id,
            tier=tier,
            cta_url=cta_url,
            analysis_slug=analysis_slug,
            created_by=actor_user_id,
        )
        created = await self._repo.create(db, post=post)
        await self._audit.write(db, actor_user_id=actor_user_id, action="post_created", meta={"post_id": str(created.id)})
        return created

    async def update_post(
        self,
        db: AsyncSession,
        *,
        actor_user_id: uuid.UUID,
        post: Post,
        text: Optional[str],
        image_url: Optional[str],
        image_mode: Optional[str],
        pillar_id: Optional[str],
        template_id: Optional[str],
        mode_id: Optional[str],
        tier: Optional[str],
        cta_url: Optional[str],
        analysis_slug: Optional[str],
    ) -> Post:
        if text is not None:
            post.text = text
        if image_url is not None:
            post.image_url = image_url
        if image_mode is not None:
            post.image_mode = image_mode
        if pillar_id is not None:
            post.pillar_id = pillar_id
        if template_id is not None:
            post.template_id = template_id
        if mode_id is not None:
            post.mode_id = mode_id
        if tier is not None:
            post.tier = tier
        if cta_url is not None:
            post.cta_url = cta_url
        if analysis_slug is not None:
            post.analysis_slug = analysis_slug

        saved = await self._repo.save(db, post=post)
        await self._audit.write(db, actor_user_id=actor_user_id, action="post_updated", meta={"post_id": str(saved.id)})
        return saved

    async def approve(self, db: AsyncSession, *, actor_user_id: uuid.UUID, post: Post) -> Optional[ComplianceError]:
        check = await self._banned.check_text(db, text=post.text)
        if not check.ok:
            return ComplianceError(matched_phrases=check.matched_phrases)
        post.status = PostStatus.approved.value
        post.error = None
        saved = await self._repo.save(db, post=post)
        await self._audit.write(db, actor_user_id=actor_user_id, action="post_approved", meta={"post_id": str(saved.id)})
        return None

    async def schedule(
        self,
        db: AsyncSession,
        *,
        actor_user_id: uuid.UUID,
        post: Post,
        scheduled_for: datetime,
        tier: str,
    ) -> Optional[ComplianceError]:
        check = await self._banned.check_text(db, text=post.text)
        if not check.ok:
            return ComplianceError(matched_phrases=check.matched_phrases)
        post.status = PostStatus.scheduled.value
        post.scheduled_for = scheduled_for
        post.tier = tier
        post.error = None
        saved = await self._repo.save(db, post=post)
        await self._audit.write(
            db,
            actor_user_id=actor_user_id,
            action="post_scheduled",
            meta={"post_id": str(saved.id), "scheduled_for": saved.scheduled_for.isoformat() if saved.scheduled_for else None, "tier": tier},
        )
        return None

    async def post_now(self, db: AsyncSession, *, actor_user_id: uuid.UUID, post: Post) -> Optional[ComplianceError]:
        return await self.schedule(
            db,
            actor_user_id=actor_user_id,
            post=post,
            scheduled_for=datetime.now(timezone.utc),
            tier=post.tier or "A",
        )

    async def retry(self, db: AsyncSession, *, actor_user_id: uuid.UUID, post: Post) -> None:
        post.status = PostStatus.scheduled.value
        post.scheduled_for = datetime.now(timezone.utc)
        post.error = None
        saved = await self._repo.save(db, post=post)
        await self._audit.write(db, actor_user_id=actor_user_id, action="post_retried", meta={"post_id": str(saved.id)})

    async def regenerate_copy(self, db: AsyncSession, *, actor_user_id: uuid.UUID, post: Post) -> Post:
        # MVP: create a new draft variant by prefixing a new hook line.
        prefixes = ["Quick note:", "Keep it simple:", "One filter before you bet:", "Bankroll check:"]
        base = (post.text or "").strip()
        lowered = base.lower()
        prefix = next((p for p in prefixes if not lowered.startswith(p.lower())), prefixes[0])
        regenerated = f"{prefix}\n\n{base}".strip()

        post.text = regenerated
        # Preserve status if post was already approved or scheduled (user may want to keep workflow)
        # Only reset to draft if it was posted or failed
        if post.status in (PostStatus.posted.value, PostStatus.failed.value):
            post.status = PostStatus.draft.value
            post.scheduled_for = None
            post.posted_at = None
            post.tweet_id = None
        # For approved/scheduled posts, keep status but clear scheduling if scheduled
        elif post.status == PostStatus.scheduled.value:
            post.status = PostStatus.approved.value  # Move to approved since we cleared scheduling
            post.scheduled_for = None
        # For draft/pending, keep as draft
        else:
            post.status = PostStatus.draft.value
        
        post.error = None

        saved = await self._repo.save(db, post=post)
        await self._audit.write(db, actor_user_id=actor_user_id, action="post_regenerate_copy", meta={"post_id": str(saved.id)})
        return saved

    async def regenerate_image(self, db: AsyncSession, *, actor_user_id: uuid.UUID, post: Post, image_mode: Optional[str]) -> Post:
        post.image_url = None
        if image_mode is not None:
            post.image_mode = image_mode
        post.status = PostStatus.draft.value
        post.error = None
        post.scheduled_for = None

        settings = get_settings()
        static_root = _resolve_static_root()
        generator = PostImageGenerator(settings=settings, static_root=static_root)
        try:
            generated = await generator.generate_for_post(
                post_id=str(post.id),
                post_text=post.text,
                pillar_id=post.pillar_id,
                template_id=post.template_id,
                requested_image_mode=image_mode or post.image_mode,
            )
            post.image_mode = generated.image_mode
            post.image_url = generated.public_url
        except ImageGenerationError as exc:
            post.error = f"image_generate_failed: {str(exc)}"[:500]

        saved = await self._repo.save(db, post=post)
        await self._audit.write(
            db,
            actor_user_id=actor_user_id,
            action="post_regenerate_image",
            meta={"post_id": str(saved.id), "image_mode": image_mode, "image_url": saved.image_url},
        )
        return saved


def _resolve_static_root() -> "Path":
    from pathlib import Path

    # This matches the mounting convention in pg_social_bot_api/main.py
    return Path(__file__).resolve().parents[2] / "static"
