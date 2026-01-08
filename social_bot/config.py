from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class ConfigError(RuntimeError):
    pass


class DotenvLoader:
    def __init__(self, *, env_path: Path) -> None:
        self._env_path = env_path

    def load_if_present(self) -> None:
        if not self._env_path.exists():
            return
        try:
            from dotenv import load_dotenv  # type: ignore

            load_dotenv(self._env_path)
        except Exception:
            # Keep dotenv optional; callers can still provide env vars.
            return


class Env:
    @staticmethod
    def optional(name: str) -> Optional[str]:
        raw = os.getenv(name)
        if raw is None:
            return None
        value = str(raw).strip()
        return value if value else None

    @staticmethod
    def require(name: str) -> str:
        value = Env.optional(name)
        if not value:
            raise ConfigError(f"Missing env var: {name}")
        return value

    @staticmethod
    def bool(name: str, default: bool) -> bool:
        raw = Env.optional(name)
        if raw is None:
            return bool(default)
        return raw.lower() in {"1", "true", "yes", "y", "on"}

    @staticmethod
    def int(name: str, default: int) -> int:
        raw = Env.optional(name)
        if raw is None:
            return int(default)
        return int(raw)

    @staticmethod
    def optional_int(name: str) -> Optional[int]:
        raw = Env.optional(name)
        if raw is None:
            return None
        try:
            return int(raw)
        except Exception:
            return None

    @staticmethod
    def float(name: str, default: float) -> float:
        raw = Env.optional(name)
        if raw is None:
            return float(default)
        return float(raw)


@dataclass(frozen=True)
class BotConfig:
    # Runtime
    dry_run: bool
    timezone: str
    log_level: str

    # Content
    analysis_feed_url: str
    frontend_url: str
    analysis_slug_reuse_cooldown_hours: int
    analysis_upcoming_window_hours: int
    humor_target_ratio: float
    include_link_probability: float
    parlay_post_max_ratio: float

    # Scheduling (config-driven)
    posting_windows_weekday: tuple[str, ...]
    posting_windows_weekend: tuple[str, ...]
    schedule_jitter_minutes: int
    no_early_post_before: str
    weekday_max_posts_per_day: int
    weekend_max_posts_per_day: int

    # OpenAI
    openai_api_key: str
    openai_model: str
    openai_base_url: str
    openai_timeout_seconds: float

    # X
    x_api_base_url: str
    x_bearer_token: str
    x_api_key: str
    x_api_secret: str
    x_access_token: str
    x_access_secret: str
    x_timeout_seconds: float

    # Storage
    memory_path: Path
    images_root: Path

    @staticmethod
    def load(*, project_root: Path) -> "BotConfig":
        # `project_root` is expected to be the repo root. Keep backward compatibility by
        # also loading `social_bot/.env` if it exists.
        DotenvLoader(env_path=project_root / ".env").load_if_present()
        bot_root = project_root / "social_bot"
        if bot_root.exists():
            DotenvLoader(env_path=bot_root / ".env").load_if_present()
        else:
            bot_root = project_root

        dry_run = Env.bool("BOT_DRY_RUN", True)
        timezone = Env.optional("BOT_TIMEZONE") or "America/Chicago"
        log_level = (Env.optional("BOT_LOG_LEVEL") or "INFO").upper()

        analysis_feed_url = Env.optional("ANALYSIS_FEED_URL") or "https://api.parlaygorilla.com/api/analysis-feed"
        frontend_url = Env.optional("FRONTEND_URL") or "https://www.parlaygorilla.com"

        cooldown_hours = Env.int("ANALYSIS_SLUG_REUSE_COOLDOWN_HOURS", 48)
        analysis_upcoming_window_hours = Env.int("ANALYSIS_UPCOMING_WINDOW_HOURS", 72)

        humor_target_ratio = Env.float("HUMOR_TARGET_RATIO", 0.22)
        include_link_probability = Env.float("INCLUDE_LINK_PROBABILITY", 0.6)
        parlay_post_max_ratio = Env.float("PARLAY_POST_MAX_RATIO", 0.10)

        # Scheduling defaults (Central Time)
        weekday_default = ("08:10", "11:40", "14:10", "17:10")
        weekend_default = ("09:05", "12:35", "18:15")

        posting_windows_weekday = _parse_time_list(
            Env.optional("POSTING_WINDOWS_WEEKDAY"), default=weekday_default
        )
        posting_windows_weekend = _parse_time_list(
            Env.optional("POSTING_WINDOWS_WEEKEND"), default=weekend_default
        )
        schedule_jitter_minutes = Env.int("SCHEDULE_JITTER_MINUTES", 8)
        no_early_post_before = (Env.optional("NO_EARLY_POST_BEFORE") or "06:30").strip()

        global_max = Env.optional_int("MAX_POSTS_PER_DAY")
        weekday_max_posts_per_day = Env.optional_int("WEEKDAY_MAX_POSTS_PER_DAY") or (
            int(global_max) if global_max is not None else 4
        )
        weekend_max_posts_per_day = Env.optional_int("WEEKEND_MAX_POSTS_PER_DAY") or (
            int(global_max) if global_max is not None else 3
        )

        openai_api_key = Env.require("OPENAI_API_KEY")
        openai_model = Env.optional("OPENAI_MODEL") or "gpt-4o-mini"
        openai_base_url = Env.optional("OPENAI_BASE_URL") or "https://api.openai.com/v1"
        openai_timeout_seconds = Env.float("OPENAI_TIMEOUT_SECONDS", 20.0)

        x_api_base_url = Env.optional("X_API_BASE_URL") or "https://api.x.com/2"
        x_bearer_token = Env.optional("X_BEARER_TOKEN") or ""
        x_api_key = Env.optional("X_API_KEY") or ""
        x_api_secret = Env.optional("X_API_SECRET") or ""
        x_access_token = Env.optional("X_ACCESS_TOKEN") or ""
        x_access_secret = Env.optional("X_ACCESS_SECRET") or ""
        x_timeout_seconds = Env.float("X_TIMEOUT_SECONDS", 20.0)

        if not dry_run and not x_bearer_token and not (x_api_key and x_api_secret and x_access_token and x_access_secret):
            raise ConfigError(
                "X credentials required when BOT_DRY_RUN=false. "
                "Set X_BEARER_TOKEN (OAuth2 user token) or X_API_KEY/X_API_SECRET/X_ACCESS_TOKEN/X_ACCESS_SECRET (OAuth1)."
            )

        memory_path = bot_root / "memory.json"
        images_root = bot_root / "images"

        return BotConfig(
            dry_run=dry_run,
            timezone=timezone,
            log_level=log_level,
            analysis_feed_url=analysis_feed_url,
            frontend_url=frontend_url,
            analysis_slug_reuse_cooldown_hours=cooldown_hours,
            analysis_upcoming_window_hours=analysis_upcoming_window_hours,
            humor_target_ratio=humor_target_ratio,
            include_link_probability=include_link_probability,
            parlay_post_max_ratio=parlay_post_max_ratio,
            posting_windows_weekday=posting_windows_weekday,
            posting_windows_weekend=posting_windows_weekend,
            schedule_jitter_minutes=schedule_jitter_minutes,
            no_early_post_before=no_early_post_before,
            weekday_max_posts_per_day=weekday_max_posts_per_day,
            weekend_max_posts_per_day=weekend_max_posts_per_day,
            openai_api_key=openai_api_key,
            openai_model=openai_model,
            openai_base_url=openai_base_url,
            openai_timeout_seconds=openai_timeout_seconds,
            x_api_base_url=x_api_base_url,
            x_bearer_token=x_bearer_token,
            x_api_key=x_api_key,
            x_api_secret=x_api_secret,
            x_access_token=x_access_token,
            x_access_secret=x_access_secret,
            x_timeout_seconds=x_timeout_seconds,
            memory_path=memory_path,
            images_root=images_root,
        )


def _parse_time_list(raw: Optional[str], *, default: tuple[str, ...]) -> tuple[str, ...]:
    """
    Parse comma-separated HH:MM strings (24-hour clock).
    Example: "08:10,11:40,14:10,17:10"
    """
    if not raw:
        return tuple(default)
    parts = [p.strip() for p in str(raw).split(",") if p.strip()]
    out: list[str] = []
    for p in parts:
        if not _is_hhmm(p):
            continue
        out.append(p)
    return tuple(out) if out else tuple(default)


def _is_hhmm(value: str) -> bool:
    s = str(value or "").strip()
    if len(s) != 5 or s[2] != ":":
        return False
    hh, mm = s.split(":", 1)
    if not (hh.isdigit() and mm.isdigit()):
        return False
    h = int(hh)
    m = int(mm)
    return 0 <= h <= 23 and 0 <= m <= 59

