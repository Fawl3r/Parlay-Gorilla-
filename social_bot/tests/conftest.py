from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

import pytest


# Ensure `import src.*` works when running tests from repo root.
SOCIAL_BOT_ROOT = Path(__file__).resolve().parents[1]
if str(SOCIAL_BOT_ROOT) not in sys.path:
    sys.path.insert(0, str(SOCIAL_BOT_ROOT))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


@pytest.fixture()
def bot_project_root(tmp_path: Path) -> Path:
    root = tmp_path / "social_bot_test"
    (root / "config").mkdir(parents=True, exist_ok=True)
    (root / "content").mkdir(parents=True, exist_ok=True)
    (root / "queue").mkdir(parents=True, exist_ok=True)
    (root / "cache").mkdir(parents=True, exist_ok=True)
    (root / "logs").mkdir(parents=True, exist_ok=True)

    _write_json(
        root / "config" / "settings.json",
        {
            "bot": {"dry_run": True, "timezone": "UTC", "log_level": "INFO"},
            "site_content": {
                "analysis_feed_url": "",
                "analysis_feed_cache_ttl_seconds": 3600,
                "slug_reuse_cooldown_hours": 48,
                "max_analysis_posts_per_day": 2,
                "redirect_base_url": "http://localhost:8000",
                "ab_variants": ["a", "b"],
                "frontend_url": "http://localhost:3000",
                "upcoming_sport": "nfl",
                "upcoming_limit": 20,
            },
            "writer": {"suggested_template_bias": 1.0, "hook_probability": 0.0, "analysis_injection_probability": 0.0, "max_generate_attempts_per_item": 4},
            "guardian": {"max_length": 280, "max_hashtags": 2, "max_emojis": 2, "banned_phrase_action": "reject"},
            "dedupe": {"similarity_threshold": 0.88, "template_cooldown_hours": 18, "pillar_cooldown_hours": 6, "recent_window_items": 50},
            "publisher": {"api_base_url": "https://api.x.com/2", "max_retries": 2, "backoff_initial_seconds": 0.0, "backoff_max_seconds": 0.0, "timeout_seconds": 1.0},
            "scheduler": {
                "max_posts_per_day": 5,
                "max_threads_per_week": 2,
                "weekday_schedule": [{"time": "09:00", "tier": "mid"}],
                "weekend_schedule": [{"time": "10:00", "tier": "mid"}],
                "tier_fallback": {"mid": ["mid", "low", "high"], "low": ["low", "mid"], "high": ["high", "mid"]},
            },
            "images": {"enabled": False},
        },
    )

    _write_json(
        root / "content" / "pillars.json",
        [
            {"id": "betting_discipline", "name": "Betting", "weight": 1.0, "suggested_templates": ["t1", "t2"]},
        ],
    )
    _write_json(
        root / "content" / "templates.json",
        [
            {"id": "t1", "type": "single", "text": "Template 1", "base_score": 60, "is_disclaimer": False, "is_analysis": False},
            {"id": "t2", "type": "single", "text": "Template 2", "base_score": 50, "is_disclaimer": False, "is_analysis": False},
        ],
    )
    _write_json(root / "content" / "hooks.json", [])
    _write_json(root / "content" / "seasonal_modes.json", [])
    _write_json(root / "content" / "banned_phrases.json", ["free money"])

    _write_json(root / "queue" / "outbox.json", [])
    _write_json(root / "queue" / "posted.json", [])
    _write_json(root / "cache" / "analysis_feed.json", {"fetched_at": None, "expires_at": None, "items": [], "used_slugs": {}})
    (root / "logs" / "bot.log").write_text("", encoding="utf-8")
    (root / "logs" / "audit.jsonl").write_text("", encoding="utf-8")

    return root


