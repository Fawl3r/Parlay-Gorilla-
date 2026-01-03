from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


class SettingsError(RuntimeError):
    pass


def _parse_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _parse_int(value: str) -> int:
    return int(str(value).strip())


def _parse_float(value: str) -> float:
    return float(str(value).strip())


@dataclass(frozen=True)
class BotSettings:
    dry_run: bool
    timezone: str
    log_level: str


@dataclass(frozen=True)
class SiteContentSettings:
    analysis_feed_url: str
    analysis_feed_cache_ttl_seconds: int
    slug_reuse_cooldown_hours: int
    max_analysis_posts_per_day: int
    redirect_base_url: str
    ab_variants: List[str]


@dataclass(frozen=True)
class WriterSettings:
    suggested_template_bias: float
    hook_probability: float
    analysis_injection_probability: float
    max_generate_attempts_per_item: int


@dataclass(frozen=True)
class GuardianSettings:
    max_length: int
    max_hashtags: int
    max_emojis: int
    banned_phrase_action: str  # reject | sanitize


@dataclass(frozen=True)
class DedupeSettings:
    similarity_threshold: float
    template_cooldown_hours: int
    pillar_cooldown_hours: int
    recent_window_items: int


@dataclass(frozen=True)
class PublisherSettings:
    api_base_url: str
    bearer_token: str
    max_retries: int
    backoff_initial_seconds: float
    backoff_max_seconds: float
    timeout_seconds: float


@dataclass(frozen=True)
class ScheduleSlot:
    time: str  # HH:MM local
    tier: str


@dataclass(frozen=True)
class SchedulerSettings:
    max_posts_per_day: int
    max_threads_per_week: int
    ensure_disclaimer_once_per_day: bool
    disclaimer_template_id: str
    weekday_schedule: List[ScheduleSlot]
    weekend_schedule: List[ScheduleSlot]
    tier_fallback: Dict[str, List[str]]


@dataclass(frozen=True)
class Settings:
    bot: BotSettings
    site_content: SiteContentSettings
    writer: WriterSettings
    guardian: GuardianSettings
    dedupe: DedupeSettings
    publisher: PublisherSettings
    scheduler: SchedulerSettings


class SettingsManager:
    def __init__(self, project_root: Optional[Path] = None) -> None:
        self._project_root = project_root or Path(__file__).resolve().parents[1]
        self._config_path = self._project_root / "config" / "settings.json"
        self._settings: Optional[Settings] = None

    @property
    def project_root(self) -> Path:
        return self._project_root

    def load(self) -> Settings:
        if self._settings is not None:
            return self._settings

        self._load_dotenv_if_present()
        raw = self._load_json(self._config_path)
        raw = self._apply_env_overrides(raw)
        self._settings = self._validate_and_build(raw)
        return self._settings

    def _load_dotenv_if_present(self) -> None:
        env_path = self._project_root / ".env"
        if not env_path.exists():
            return
        try:
            from dotenv import load_dotenv  # type: ignore

            load_dotenv(env_path)
        except Exception:
            # dotenv is optional; env vars can still be supplied by the shell
            return

    def _load_json(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            raise SettingsError(f"Missing settings file: {path}")
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise SettingsError(f"Failed to parse settings JSON: {path}") from exc

    def _apply_env_overrides(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        def set_path(target: Dict[str, Any], path: str, value: Any) -> None:
            parts = path.split(".")
            node: Dict[str, Any] = target
            for key in parts[:-1]:
                if key not in node or not isinstance(node[key], dict):
                    node[key] = {}
                node = node[key]
            node[parts[-1]] = value

        mapping = {
            "BOT_DRY_RUN": ("bot.dry_run", _parse_bool),
            "BOT_TIMEZONE": ("bot.timezone", str),
            "BOT_LOG_LEVEL": ("bot.log_level", str),
            "X_BEARER_TOKEN": ("publisher.bearer_token", str),
            "X_API_BASE_URL": ("publisher.api_base_url", str),
            "ANALYSIS_FEED_URL": ("site_content.analysis_feed_url", str),
            "ANALYSIS_FEED_CACHE_TTL_SECONDS": ("site_content.analysis_feed_cache_ttl_seconds", _parse_int),
            "ANALYSIS_SLUG_REUSE_COOLDOWN_HOURS": ("site_content.slug_reuse_cooldown_hours", _parse_int),
            "REDIRECT_BASE_URL": ("site_content.redirect_base_url", str),
        }

        merged = json.loads(json.dumps(raw))  # deep copy (JSON-safe)
        for env_key, (path, caster) in mapping.items():
            if env_key not in os.environ:
                continue
            try:
                set_path(merged, path, caster(os.environ[env_key]))
            except Exception as exc:
                raise SettingsError(f"Invalid env override {env_key}") from exc
        return merged

    def _validate_and_build(self, raw: Dict[str, Any]) -> Settings:
        bot_raw = raw.get("bot") or {}
        site_raw = raw.get("site_content") or {}
        writer_raw = raw.get("writer") or {}
        guardian_raw = raw.get("guardian") or {}
        dedupe_raw = raw.get("dedupe") or {}
        publisher_raw = raw.get("publisher") or {}
        scheduler_raw = raw.get("scheduler") or {}

        bot = BotSettings(
            dry_run=bool(bot_raw.get("dry_run", True)),
            timezone=str(bot_raw.get("timezone") or "UTC"),
            log_level=str(bot_raw.get("log_level") or "INFO"),
        )

        site = SiteContentSettings(
            analysis_feed_url=str(site_raw.get("analysis_feed_url") or "").strip(),
            analysis_feed_cache_ttl_seconds=int(site_raw.get("analysis_feed_cache_ttl_seconds") or 43200),
            slug_reuse_cooldown_hours=int(site_raw.get("slug_reuse_cooldown_hours") or 48),
            max_analysis_posts_per_day=int(site_raw.get("max_analysis_posts_per_day") or 0),
            redirect_base_url=str(site_raw.get("redirect_base_url") or "").strip(),
            ab_variants=[str(x) for x in (site_raw.get("ab_variants") or ["a", "b"])],
        )

        writer = WriterSettings(
            suggested_template_bias=float(writer_raw.get("suggested_template_bias") or 0.7),
            hook_probability=float(writer_raw.get("hook_probability") or 0.0),
            analysis_injection_probability=float(writer_raw.get("analysis_injection_probability") or 0.0),
            max_generate_attempts_per_item=int(writer_raw.get("max_generate_attempts_per_item") or 8),
        )

        guardian = GuardianSettings(
            max_length=int(guardian_raw.get("max_length") or 280),
            max_hashtags=int(guardian_raw.get("max_hashtags") or 0),
            max_emojis=int(guardian_raw.get("max_emojis") or 0),
            banned_phrase_action=str(guardian_raw.get("banned_phrase_action") or "reject").strip().lower(),
        )

        dedupe = DedupeSettings(
            similarity_threshold=float(dedupe_raw.get("similarity_threshold") or 0.9),
            template_cooldown_hours=int(dedupe_raw.get("template_cooldown_hours") or 0),
            pillar_cooldown_hours=int(dedupe_raw.get("pillar_cooldown_hours") or 0),
            recent_window_items=int(dedupe_raw.get("recent_window_items") or 50),
        )

        publisher = PublisherSettings(
            api_base_url=str(publisher_raw.get("api_base_url") or "").strip(),
            bearer_token=str(publisher_raw.get("bearer_token") or os.environ.get("X_BEARER_TOKEN", "")).strip(),
            max_retries=int(publisher_raw.get("max_retries") or 3),
            backoff_initial_seconds=float(publisher_raw.get("backoff_initial_seconds") or 1.0),
            backoff_max_seconds=float(publisher_raw.get("backoff_max_seconds") or 30.0),
            timeout_seconds=float(publisher_raw.get("timeout_seconds") or 10.0),
        )

        weekday_slots = self._build_slots(scheduler_raw.get("weekday_schedule") or [])
        weekend_slots = self._build_slots(scheduler_raw.get("weekend_schedule") or [])
        scheduler = SchedulerSettings(
            max_posts_per_day=int(scheduler_raw.get("max_posts_per_day") or 0),
            max_threads_per_week=int(scheduler_raw.get("max_threads_per_week") or 0),
            ensure_disclaimer_once_per_day=bool(scheduler_raw.get("ensure_disclaimer_once_per_day", True)),
            disclaimer_template_id=str(scheduler_raw.get("disclaimer_template_id") or "daily_disclaimer").strip(),
            weekday_schedule=weekday_slots,
            weekend_schedule=weekend_slots,
            tier_fallback={str(k): [str(x) for x in v] for k, v in (scheduler_raw.get("tier_fallback") or {}).items()},
        )

        self._validate_invariants(bot, site, writer, guardian, dedupe, publisher, scheduler)
        return Settings(
            bot=bot,
            site_content=site,
            writer=writer,
            guardian=guardian,
            dedupe=dedupe,
            publisher=publisher,
            scheduler=scheduler,
        )

    def _build_slots(self, raw_slots: List[Dict[str, Any]]) -> List[ScheduleSlot]:
        slots: List[ScheduleSlot] = []
        for raw in raw_slots:
            slots.append(ScheduleSlot(time=str(raw.get("time") or "").strip(), tier=str(raw.get("tier") or "").strip()))
        return slots

    def _validate_invariants(
        self,
        bot: BotSettings,
        site: SiteContentSettings,
        writer: WriterSettings,
        guardian: GuardianSettings,
        dedupe: DedupeSettings,
        publisher: PublisherSettings,
        scheduler: SchedulerSettings,
    ) -> None:
        if guardian.banned_phrase_action not in {"reject", "sanitize"}:
            raise SettingsError("guardian.banned_phrase_action must be 'reject' or 'sanitize'")

        if not publisher.api_base_url:
            raise SettingsError("publisher.api_base_url is required")

        if not bot.dry_run and not publisher.bearer_token:
            raise SettingsError("X credentials required: set X_BEARER_TOKEN or enable bot.dry_run")

        if not site.analysis_feed_url:
            # Analysis injection can still be disabled; keep this as a soft warning.
            return

        for slot in scheduler.weekday_schedule + scheduler.weekend_schedule:
            if not slot.time or ":" not in slot.time:
                raise SettingsError(f"Invalid schedule time: {slot.time}")


