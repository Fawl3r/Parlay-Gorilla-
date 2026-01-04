from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from typing import List, Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from pg_social_bot_api.admin.audit_logger import AuditLogger
from pg_social_bot_api.admin.content_repository import ContentRepository
from pg_social_bot_api.admin.upstream_feed_client import UpstreamAnalysisItem, UpstreamFeedClient
from pg_social_bot_api.core.config import Settings, get_settings
from pg_social_bot_api.models.analysis_item_cache import AnalysisItemCache
from pg_social_bot_api.models.enums import PostStatus
from pg_social_bot_api.models.post import Post


@dataclass(frozen=True)
class CachedAnalysisItem:
    slug: str
    angle: str
    key_points: list[str]
    risk_note: Optional[str]
    cta_url: str
    last_seen_at: str


class AnalysisService:
    def __init__(self, *, settings: Optional[Settings] = None) -> None:
        self._settings = settings or get_settings()
        self._audit = AuditLogger()
        self._content = ContentRepository()

    async def list_cached(self, db: AsyncSession, *, limit: int = 50) -> List[CachedAnalysisItem]:
        res = await db.execute(
            select(AnalysisItemCache).order_by(desc(AnalysisItemCache.last_seen_at)).limit(int(limit))
        )
        rows = list(res.scalars().all())
        items: List[CachedAnalysisItem] = []
        for r in rows:
            items.append(
                CachedAnalysisItem(
                    slug=r.slug,
                    angle=r.angle,
                    key_points=[str(x) for x in (r.key_points or [])][:5],
                    risk_note=r.risk_note,
                    cta_url=r.cta_url,
                    last_seen_at=r.last_seen_at.isoformat(),
                )
            )
        return items

    async def refresh_from_upstream(self, db: AsyncSession, *, actor_user_id: uuid.UUID) -> int:
        url = (self._settings.upstream_analysis_feed_url or "").strip()
        if not url:
            raise ValueError(
                "UPSTREAM_ANALYSIS_FEED_URL is not configured. "
                "Set this environment variable to the URL of your analysis feed endpoint."
            )
        # Extract production frontend base URL from redirect fallback (remove /analysis suffix if present)
        redirect_base = (self._settings.redirect_fallback_base_url or "").strip().rstrip("/")
        production_frontend = redirect_base.rsplit("/analysis", 1)[0] if "/analysis" in redirect_base else redirect_base
        
        client = UpstreamFeedClient(url=url, production_frontend_url=production_frontend)
        try:
            items = await client.fetch()
        except ValueError as e:
            # Re-raise ValueError with clear message
            raise
        except Exception as e:
            raise ValueError(f"Unexpected error fetching analysis feed: {str(e)}") from e
        
        now = datetime.now(timezone.utc)

        changed = 0
        for item in items:
            changed += await self._upsert_one(db, item=item, now=now)

        await db.commit()
        await self._audit.write(
            db,
            actor_user_id=actor_user_id,
            action="analysis_refresh",
            meta={"count": len(items), "upserted": changed},
        )
        return len(items)

    async def generate_post_from_slug(self, db: AsyncSession, *, actor_user_id: uuid.UUID, slug: str) -> Post:
        slug_norm = (slug or "").strip()
        if not slug_norm:
            raise ValueError("slug is required")

        cache = await self._get_cache(db, slug=slug_norm)
        if not cache:
            raise ValueError("analysis item not found in cache")

        if await self._analysis_cap_reached_today(db):
            raise ValueError("daily analysis post cap reached")

        variant = await self._choose_variant(db, analysis_slug=slug_norm)
        url = f"{self._settings.public_origin()}/r/{slug_norm}?v={variant.lower()}"

        kp = [str(x).strip() for x in (cache.key_points or []) if str(x).strip()]
        kp1 = kp[0] if len(kp) > 0 else "Matchup context matters more than vibes."
        kp2 = kp[1] if len(kp) > 1 else "Price discipline beats hot takes over time."

        # Choose template id based on risk note presence.
        template_id = "analysis_risk_note" if cache.risk_note else "analysis_matchup_angle"
        text = await self._render_analysis_template(
            db,
            template_id=template_id,
            angle=cache.angle,
            kp1=kp1,
            kp2=kp2,
            risk_note=cache.risk_note,
            url=url,
        )

        post = Post(
            status=PostStatus.draft.value,
            text=text,
            pillar_id="analysis_excerpts",
            template_id=template_id,
            mode_id="default",
            tier="A",
            cta_url=url,
            analysis_slug=slug_norm,
            variant=variant,
            created_by=actor_user_id,
        )
        db.add(post)
        await db.commit()
        await db.refresh(post)

        await self._audit.write(
            db,
            actor_user_id=actor_user_id,
            action="analysis_generate_post",
            meta={"post_id": str(post.id), "slug": slug_norm, "variant": variant},
        )
        return post

    async def _get_cache(self, db: AsyncSession, *, slug: str) -> Optional[AnalysisItemCache]:
        res = await db.execute(select(AnalysisItemCache).where(AnalysisItemCache.slug == slug))
        return res.scalar_one_or_none()

    async def _analysis_cap_reached_today(self, db: AsyncSession) -> bool:
        cap = int(self._settings.max_analysis_posts_per_day)
        if cap <= 0:
            return False
        start = datetime.combine(date.today(), time.min).replace(tzinfo=timezone.utc)
        end = datetime.combine(date.today(), time.max).replace(tzinfo=timezone.utc)
        res = await db.execute(
            select(func.count(Post.id)).where(
                and_(Post.analysis_slug.is_not(None), Post.created_at >= start, Post.created_at <= end)
            )
        )
        count = int(res.scalar() or 0)
        return count >= cap

    async def _choose_variant(self, db: AsyncSession, *, analysis_slug: str) -> str:
        # Prefer alternating A/B per analysis_slug.
        res = await db.execute(
            select(Post.variant)
            .where(and_(Post.analysis_slug == analysis_slug, Post.variant.is_not(None)))
            .order_by(desc(Post.created_at))
            .limit(1)
        )
        last = (res.scalar_one_or_none() or "").strip().upper()
        if last == "A":
            return "B"
        return "A"

    async def _upsert_one(self, db: AsyncSession, *, item: UpstreamAnalysisItem, now: datetime) -> int:
        existing = await self._get_cache(db, slug=item.slug)
        if existing:
            existing.angle = item.angle or existing.angle
            existing.key_points = list(item.key_points or [])
            existing.risk_note = item.risk_note
            existing.cta_url = item.cta_url or existing.cta_url
            existing.last_seen_at = now
            return 1

        db.add(
            AnalysisItemCache(
                slug=item.slug,
                sport="unknown",
                matchup=item.slug,
                angle=item.angle,
                key_points=list(item.key_points or []),
                risk_note=item.risk_note,
                cta_url=item.cta_url or f"{self._settings.redirect_fallback_base_url.rstrip('/')}/{item.slug}",
                published_at=None,
                last_seen_at=now,
            )
        )
        return 1

    async def _render_analysis_template(
        self,
        db: AsyncSession,
        *,
        template_id: str,
        angle: str,
        kp1: str,
        kp2: str,
        risk_note: Optional[str],
        url: str,
    ) -> str:
        template_text = await self._get_template_text(db, template_id=template_id)
        tokens = {
            "angle": angle,
            "kp1": kp1,
            "kp2": kp2,
            "risk_note": risk_note or "",
            "url": url,
        }

        class _SafeDict(dict):
            def __missing__(self, key: str) -> str:  # type: ignore[override]
                return ""

        try:
            return str(template_text).format_map(_SafeDict(tokens)).strip()
        except Exception:
            # Fall back to a known-safe rendering.
            if template_id == "analysis_risk_note":
                return (
                    f"{angle}\n\nKey points:\n- {kp1}\n- {kp2}\n\nRisk note: {risk_note or ''}\n\nRead: {url}"
                ).strip()
            return (f"{angle}\n\nKey points:\n- {kp1}\n- {kp2}\n\nRead: {url}").strip()

    async def _get_template_text(self, db: AsyncSession, *, template_id: str) -> str:
        raw = await self._content.get_latest_json(db, content_type="templates")
        if isinstance(raw, list):
            for item in raw:
                if not isinstance(item, dict):
                    continue
                if str(item.get("id") or "").strip() == template_id:
                    text = str(item.get("text") or "").strip()
                    if text:
                        return text
        # Default fallback aligned with default_content.
        if template_id == "analysis_risk_note":
            return "{angle}\n\nKey points:\n- {kp1}\n- {kp2}\n\nRisk note: {risk_note}\n\nRead: {url}"
        return "{angle}\n\nKey points:\n- {kp1}\n- {kp2}\n\nRead: {url}"


