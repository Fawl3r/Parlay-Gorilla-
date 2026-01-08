from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from social_bot.memory_store import BotMemory, MemoryStore, utc_now


def test_memory_store_records_and_counts_today(tmp_path: Path) -> None:
    store = MemoryStore(path=tmp_path / "memory.json", timezone_name="America/New_York")
    mem = BotMemory.empty()
    now = utc_now()

    mem = store.record_post(
        mem,
        now=now,
        post_type="edge_explainer",
        text="hello",
        tweet_id="t1",
        analysis_slug=None,
        humor_allowed=False,
        media_path=None,
    )
    store.save(mem)
    loaded = store.load()
    assert store.posts_today_count(loaded, now=now) == 1


def test_slug_reuse_block(tmp_path: Path) -> None:
    store = MemoryStore(path=tmp_path / "memory.json", timezone_name="UTC")
    mem = BotMemory.empty()
    now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    mem = store.record_post(
        mem,
        now=now,
        post_type="trap_alert",
        text="x",
        tweet_id="t1",
        analysis_slug="nba/game-1",
        humor_allowed=False,
        media_path=None,
    )
    assert store.slug_used_within_hours(mem, slug="nba/game-1", hours=48, now=now) is True
    later = datetime(2026, 1, 4, 13, 0, tzinfo=timezone.utc)
    assert store.slug_used_within_hours(mem, slug="nba/game-1", hours=48, now=later) is False


def test_humor_ratio_recent(tmp_path: Path) -> None:
    store = MemoryStore(path=tmp_path / "memory.json", timezone_name="UTC")
    mem = BotMemory.empty()
    now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    mem = store.record_post(mem, now=now, post_type="a", text="1", tweet_id="t1", analysis_slug=None, humor_allowed=True, media_path="images/general/1.png")
    mem = store.record_post(mem, now=now, post_type="a", text="2", tweet_id="t2", analysis_slug=None, humor_allowed=False, media_path="images/general/2.png")
    assert store.humor_ratio_recent(mem, window=10) == 0.5


def test_recent_media_paths(tmp_path: Path) -> None:
    store = MemoryStore(path=tmp_path / "memory.json", timezone_name="UTC")
    mem = BotMemory.empty()
    now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    mem = store.record_post(mem, now=now, post_type="a", text="1", tweet_id="t1", analysis_slug=None, humor_allowed=True, media_path="images/a.png")
    mem = store.record_post(mem, now=now, post_type="a", text="2", tweet_id="t2", analysis_slug=None, humor_allowed=False, media_path="images/b.png")
    assert store.recent_media_paths(mem, limit=8) == ["images/a.png", "images/b.png"]


