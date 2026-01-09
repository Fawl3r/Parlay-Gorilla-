from __future__ import annotations

import argparse
import logging
import random
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from zoneinfo import ZoneInfo

from social_bot.config import BotConfig
from social_bot.image_library import ImageLibrary, ensure_image_folders
from social_bot.memory_store import MemoryStore, utc_now
from social_bot.post_generator import PostType, build_default_post_generator
from social_bot.poster import XPoster, build_oauth1_signer


@dataclass(frozen=True)
class RunResult:
    ok: bool
    detail: str


class BotRunner:
    def __init__(self, *, cfg: BotConfig, store: MemoryStore, logger: logging.Logger) -> None:
        self._cfg = cfg
        self._store = store
        self._logger = logger

    def run_once(self, *, force_type: Optional[PostType], seed: Optional[int], print_only: bool) -> RunResult:
        now = utc_now()
        memory = self._store.load()

        today_count = self._store.posts_today_count(memory, now=now)
        now_local = now.astimezone(ZoneInfo(self._cfg.timezone))
        cap = (
            int(self._cfg.weekend_max_posts_per_day)
            if now_local.weekday() >= 5
            else int(self._cfg.weekday_max_posts_per_day)
        )
        if today_count >= cap:
            msg = f"Daily cap reached ({today_count}/{cap}); skipping."
            self._logger.info(msg)
            return RunResult(ok=True, detail=msg)

        rng = random.Random(seed if seed is not None else int(now.timestamp()))
        decider, generator = build_default_post_generator(cfg=self._cfg, store=self._store)

        base_plan = decider.choose(memory=memory, rng=rng, now=now, force=force_type)
        plan = generator.build_plan(base=base_plan, memory=memory, rng=rng, now=now)

        self._logger.info("Selected post_type=%s include_link=%s humor_allowed=%s", plan.post_type.value, plan.include_link, plan.humor_allowed)
        generated = generator.generate(plan=plan, max_attempts=4)

        if print_only:
            print(generated.text)
            return RunResult(ok=True, detail="Printed post (no publish).")

        # Pick image (manual library) according to rules. Never crash if missing.
        # Prioritize main/ folder for Parlay Gorilla branded images
        image_lib = ImageLibrary(images_root=self._cfg.images_root, store=self._store)
        # Always attach images for better engagement (main folder has branded images)
        always_attach = True  # Always try to attach an image (especially from main/)
        choice = image_lib.choose(
            post_type=plan.post_type,
            analysis_slug=generated.analysis_slug,
            analysis_league=(plan.analysis_items[0].league if plan.analysis_items else None),
            memory=memory,
            rng=rng,
            always_attach=always_attach,
            attach_probability=1.0,  # Always try to attach if image available
        )
        image_path = choice.path if choice else None
        media_path = choice.memory_path if choice else None

        poster = self._build_poster()
        publish = poster.post(text=generated.text, image_path=image_path)
        if not publish.success or not publish.tweet_id:
            msg = f"Publish failed: {publish.error or 'unknown_error'}"
            self._logger.error(msg)
            return RunResult(ok=False, detail=msg)

        # Print post text in dry-run mode so user can see what would be posted
        if self._cfg.dry_run:
            print("\n" + "=" * 60)
            print("DRY RUN - Generated Post:")
            print("=" * 60)
            print(generated.text)
            if image_path:
                print(f"\n[Image] {media_path or str(image_path)}")
            print("=" * 60 + "\n")

        updated = self._store.record_post(
            memory,
            now=now,
            post_type=generated.post_type.value,
            text=generated.text,
            tweet_id=publish.tweet_id,
            analysis_slug=generated.analysis_slug,
            humor_allowed=generated.humor_allowed,
            media_path=media_path,
        )
        self._store.save(updated)
        msg = f"Posted tweet_id={publish.tweet_id}"
        self._logger.info(msg)
        return RunResult(ok=True, detail=msg)

    def _build_poster(self) -> XPoster:
        oauth1 = build_oauth1_signer(
            api_key=self._cfg.x_api_key,
            api_secret=self._cfg.x_api_secret,
            access_token=self._cfg.x_access_token,
            access_secret=self._cfg.x_access_secret,
        )
        return XPoster(
            dry_run=self._cfg.dry_run,
            api_base_url=self._cfg.x_api_base_url,
            bearer_token=self._cfg.x_bearer_token,
            oauth1=oauth1,
            timeout_seconds=self._cfg.x_timeout_seconds,
        )


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Parlay Gorilla simple X social bot (one post per run).")
    p.add_argument("--print-only", action="store_true", help="Generate a post and print it without posting.")
    p.add_argument("--seed", type=int, default=None, help="Deterministic RNG seed for debugging.")
    p.add_argument(
        "--force-type",
        choices=[t.value for t in PostType],
        default=None,
        help="Force a specific post type for this run.",
    )
    p.add_argument("--show-posts", type=int, default=None, metavar="N", help="Show the last N posts from memory.json (default: show all).")
    p.add_argument("--run-schedule", action="store_true", help="Run on a Central Time schedule with jitter (continuous loop).")
    return p.parse_args()


def _build_logger(level: str) -> logging.Logger:
    logger = logging.getLogger("social_bot_v2")
    if not logger.handlers:
        logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    return logger


def main() -> int:
    # Repo root (loads `.env` from here per spec; config also supports `social_bot/.env` as fallback)
    project_root = Path(__file__).resolve().parents[1]
    args = _parse_args()
    cfg = BotConfig.load(project_root=project_root)
    logger = _build_logger(cfg.log_level)

    store = MemoryStore(path=cfg.memory_path, timezone_name=cfg.timezone)

    # Ensure image folder structure exists (safe no-op if already present).
    ensure_image_folders(cfg.images_root)

    # Handle --show-posts flag
    if args.show_posts is not None:
        memory = store.load()
        posts = memory.posts
        if args.show_posts > 0:
            posts = posts[-args.show_posts:]
        if not posts:
            print("No posts found in memory.json")
            return 0
        print(f"\n{'=' * 60}")
        print(f"Showing {len(posts)} post(s) from memory.json:")
        print("=" * 60)
        for i, post in enumerate(reversed(posts), 1):
            print(f"\n[{i}] {post.post_type} - {post.ts_iso}")
            print(f"Tweet ID: {post.tweet_id}")
            if post.analysis_slug:
                print(f"Analysis: {post.analysis_slug}")
            if getattr(post, "media_path", None):
                print(f"Media: {post.media_path}")
            print(f"Length: {len(post.text)} chars")
            print("-" * 60)
            print(post.text)
            print("-" * 60)
        print("=" * 60 + "\n")
        return 0

    if args.run_schedule:
        _run_schedule(cfg=cfg, store=store, logger=logger)
        return 0

    runner = BotRunner(cfg=cfg, store=store, logger=logger)

    force = PostType(args.force_type) if args.force_type else None
    result = runner.run_once(force_type=force, seed=args.seed, print_only=bool(args.print_only))
    return 0 if result.ok else 1


def _run_schedule(*, cfg: BotConfig, store: MemoryStore, logger: logging.Logger) -> None:
    """
    Central Time schedule (with jitter) intended for running in a long-lived process (cron/worker/container).

    Rules:
    - Weekdays: 08:10, 11:40, 14:10, optional 17:10
    - Weekends: 09:05, 12:35, optional 18:15
    - Add jitter ±8 minutes
    - Never post before 6:30 AM local
    - If behind schedule, skip (no catch-up)
    - On 429, back off 20–40 minutes and retry once
    """
    tz = ZoneInfo(cfg.timezone)
    rng = random.Random()
    runner = BotRunner(cfg=cfg, store=store, logger=logger)

    min_time = _parse_hhmm(cfg.no_early_post_before, fallback=(6, 30))
    jitter_minutes = int(cfg.schedule_jitter_minutes)

    weekday_base = [_parse_hhmm(x, fallback=None) for x in cfg.posting_windows_weekday]
    weekend_base = [_parse_hhmm(x, fallback=None) for x in cfg.posting_windows_weekend]
    weekday_base = [x for x in weekday_base if x is not None]
    weekend_base = [x for x in weekend_base if x is not None]

    def _is_weekend(dt: datetime) -> bool:
        return dt.weekday() >= 5

    def _apply_jitter(dt: datetime) -> datetime:
        if jitter_minutes <= 0:
            return dt
        offset = rng.randint(-jitter_minutes, jitter_minutes)
        return dt + timedelta(minutes=offset)

    def _clamp_min(dt: datetime) -> datetime:
        floor = dt.replace(hour=min_time[0], minute=min_time[1], second=0, microsecond=0)
        return dt if dt >= floor else floor

    def _today_slots(now_local: datetime) -> list[datetime]:
        base = weekend_base if _is_weekend(now_local) else weekday_base
        slots: list[datetime] = []
        for hh, mm in base:
            dt = now_local.replace(hour=hh, minute=mm, second=0, microsecond=0)
            dt = _apply_jitter(dt)
            dt = _clamp_min(dt)
            slots.append(dt)
        # Ensure monotonically increasing (jitter can reorder)
        return sorted(slots)

    def _max_posts_for_day(now_local: datetime) -> int:
        return int(cfg.weekend_max_posts_per_day) if _is_weekend(now_local) else int(cfg.weekday_max_posts_per_day)

    while True:
        now_utc = utc_now()
        now_local = now_utc.astimezone(tz)
        slots = _today_slots(now_local)

        # Respect daily cap (and don't "catch up").
        mem = store.load()
        posted_today = store.posts_today_count(mem, now=now_utc)
        cap = _max_posts_for_day(now_local)
        if posted_today >= cap:
            # Sleep until just after midnight local, then recalc.
            tomorrow = (now_local + timedelta(days=1)).replace(hour=0, minute=1, second=0, microsecond=0)
            sleep_for = max(30.0, (tomorrow - now_local).total_seconds())
            logger.info("Schedule cap reached (%s/%s). Sleeping until next day.", posted_today, cap)
            time.sleep(sleep_for)
            continue

        # Find next slot (skip any already passed; no catch-up posting).
        next_slot = next((s for s in slots if s > now_local), None)
        if next_slot is None:
            # No remaining slots today; sleep until tomorrow.
            tomorrow = (now_local + timedelta(days=1)).replace(hour=0, minute=1, second=0, microsecond=0)
            sleep_for = max(30.0, (tomorrow - now_local).total_seconds())
            logger.info("No remaining slots today. Sleeping until next day.")
            time.sleep(sleep_for)
            continue

        sleep_for = max(1.0, (next_slot - now_local).total_seconds())
        logger.info("Next scheduled slot at %s (%s). Sleeping %ss.", next_slot.strftime("%Y-%m-%d %H:%M"), cfg.timezone, int(sleep_for))
        time.sleep(sleep_for)

        # Attempt post.
        result = runner.run_once(force_type=None, seed=None, print_only=False)
        if result.ok:
            continue

        # Rate limit backoff + one retry.
        if "429" in result.detail:
            backoff = rng.randint(20, 40) * 60
            logger.warning("Rate limited; backing off %ss then retrying once.", backoff)
            time.sleep(backoff)
            retry = runner.run_once(force_type=None, seed=None, print_only=False)
            if not retry.ok:
                logger.error("Retry after rate limit failed: %s", retry.detail)
        else:
            logger.error("Scheduled post failed: %s", result.detail)


def _parse_hhmm(value: str, fallback: Optional[tuple[int, int]]) -> Optional[tuple[int, int]]:
    s = str(value or "").strip()
    if len(s) != 5 or s[2] != ":":
        return fallback
    hh, mm = s.split(":", 1)
    if not (hh.isdigit() and mm.isdigit()):
        return fallback
    h = int(hh)
    m = int(mm)
    if not (0 <= h <= 23 and 0 <= m <= 59):
        return fallback
    return (h, m)


if __name__ == "__main__":
    raise SystemExit(main())


