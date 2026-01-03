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
    frontend_url: str
    upcoming_sport: str
    upcoming_limit: int


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
    media_upload_url: str
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
    weekday_schedule: List[ScheduleSlot]
    weekend_schedule: List[ScheduleSlot]
    tier_fallback: Dict[str, List[str]]

@dataclass(frozen=True)
class ImageValidationSettings:
    enabled: bool
    provider: str
    model: str
    max_attempts: int


@dataclass(frozen=True)
class ImagesSettings:
    enabled: bool
    provider: str
    output_dir: str
    image_size: List[int]
    attach_to_post_probability: float
    force_for_templates: List[str]
    logo_path: str
    font_path: str
    character_spec_path: str
    validation: ImageValidationSettings
    openai_api_key: str


@dataclass(frozen=True)
class Settings:
    bot: BotSettings
    site_content: SiteContentSettings
    writer: WriterSettings
    guardian: GuardianSettings
    dedupe: DedupeSettings
    publisher: PublisherSettings
    scheduler: SchedulerSettings
    images: ImagesSettings


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
            "X_MEDIA_UPLOAD_URL": ("publisher.media_upload_url", str),
            "ANALYSIS_FEED_URL": ("site_content.analysis_feed_url", str),
            "ANALYSIS_FEED_CACHE_TTL_SECONDS": ("site_content.analysis_feed_cache_ttl_seconds", _parse_int),
            "ANALYSIS_SLUG_REUSE_COOLDOWN_HOURS": ("site_content.slug_reuse_cooldown_hours", _parse_int),
            "REDIRECT_BASE_URL": ("site_content.redirect_base_url", str),
            "FRONTEND_URL": ("site_content.frontend_url", str),
            "UPCOMING_SPORT": ("site_content.upcoming_sport", str),
            "UPCOMING_LIMIT": ("site_content.upcoming_limit", _parse_int),
            "IMAGES_ENABLED": ("images.enabled", _parse_bool),
            "IMAGES_PROVIDER": ("images.provider", str),
            "IMAGES_OUTPUT_DIR": ("images.output_dir", str),
            "IMAGES_ATTACH_PROBABILITY": ("images.attach_to_post_probability", _parse_float),
            "IMAGES_LOGO_PATH": ("images.logo_path", str),
            "IMAGES_FONT_PATH": ("images.font_path", str),
            "IMAGES_CHARACTER_SPEC_PATH": ("images.character_spec_path", str),
            "IMAGES_VALIDATION_ENABLED": ("images.validation.enabled", _parse_bool),
            "IMAGES_VALIDATION_PROVIDER": ("images.validation.provider", str),
            "IMAGES_VALIDATION_MODEL": ("images.validation.model", str),
            "IMAGES_VALIDATION_MAX_ATTEMPTS": ("images.validation.max_attempts", _parse_int),
            "OPENAI_API_KEY": ("images.openai_api_key", str),
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
        images_raw = raw.get("images") or {}

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
            frontend_url=str(site_raw.get("frontend_url") or "https://www.parlaygorilla.com").strip(),
            upcoming_sport=str(site_raw.get("upcoming_sport") or "nfl").strip().lower(),
            upcoming_limit=int(site_raw.get("upcoming_limit") or 20),
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
            media_upload_url=str(publisher_raw.get("media_upload_url") or os.environ.get("X_MEDIA_UPLOAD_URL", "")).strip(),
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
            weekday_schedule=weekday_slots,
            weekend_schedule=weekend_slots,
            tier_fallback={str(k): [str(x) for x in v] for k, v in (scheduler_raw.get("tier_fallback") or {}).items()},
        )

        validation_raw = images_raw.get("validation") or {}
        validation = ImageValidationSettings(
            enabled=bool(validation_raw.get("enabled", False)),
            provider=str(validation_raw.get("provider") or "openai").strip().lower(),
            model=str(validation_raw.get("model") or "gpt-4o-mini").strip(),
            max_attempts=int(validation_raw.get("max_attempts") or 1),
        )

        images = ImagesSettings(
            enabled=bool(images_raw.get("enabled", False)),
            provider=str(images_raw.get("provider") or "openai").strip().lower(),
            output_dir=str(images_raw.get("output_dir") or "images/generated").strip(),
            image_size=[int(x) for x in (images_raw.get("image_size") or [1080, 1080])],
            attach_to_post_probability=float(images_raw.get("attach_to_post_probability") or 0.0),
            force_for_templates=[str(x) for x in (images_raw.get("force_for_templates") or [])],
            logo_path=str(images_raw.get("logo_path") or "").strip(),
            font_path=str(images_raw.get("font_path") or "").strip(),
            character_spec_path=str(images_raw.get("character_spec_path") or "").strip(),
            validation=validation,
            openai_api_key=str(images_raw.get("openai_api_key") or os.environ.get("OPENAI_API_KEY", "")).strip(),
        )

        self._validate_invariants(bot, site, writer, guardian, dedupe, publisher, scheduler, images)
        return Settings(
            bot=bot,
            site_content=site,
            writer=writer,
            guardian=guardian,
            dedupe=dedupe,
            publisher=publisher,
            scheduler=scheduler,
            images=images,
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
        images: ImagesSettings,
    ) -> None:
        if guardian.banned_phrase_action not in {"reject", "sanitize"}:
            raise SettingsError("guardian.banned_phrase_action must be 'reject' or 'sanitize'")

        if not publisher.api_base_url:
            raise SettingsError("publisher.api_base_url is required")

        if not bot.dry_run and not publisher.bearer_token:
            raise SettingsError("X credentials required: set X_BEARER_TOKEN or enable bot.dry_run")

        if images.enabled:
            if images.provider not in {"openai"}:
                raise SettingsError("images.provider must be 'openai'")
            if len(images.image_size) != 2 or any(int(x) <= 0 for x in images.image_size):
                raise SettingsError("images.image_size must be a 2-item array of positive ints")
            if not (0.0 <= float(images.attach_to_post_probability) <= 1.0):
                raise SettingsError("images.attach_to_post_probability must be between 0 and 1")
            if not images.output_dir:
                raise SettingsError("images.output_dir is required when images.enabled=true")
            if not images.logo_path:
                raise SettingsError("images.logo_path is required when images.enabled=true")
            # font_path is optional at runtime (we fall back), but keep config explicit.
            if not images.font_path:
                raise SettingsError("images.font_path is required when images.enabled=true")
            if images.provider == "openai" and not images.openai_api_key:
                raise SettingsError("OPENAI_API_KEY is required when images.provider=openai and images.enabled=true")
            if images.validation.enabled:
                if images.validation.provider not in {"openai"}:
                    raise SettingsError("images.validation.provider must be 'openai'")
                if not images.validation.model:
                    raise SettingsError("images.validation.model is required when images.validation.enabled=true")
                if int(images.validation.max_attempts) < 1 or int(images.validation.max_attempts) > 6:
                    raise SettingsError("images.validation.max_attempts must be between 1 and 6")
                if not images.character_spec_path:
                    raise SettingsError("images.character_spec_path is required when images.validation.enabled=true")

        for slot in scheduler.weekday_schedule + scheduler.weekend_schedule:
            if not slot.time or ":" not in slot.time:
                raise SettingsError(f"Invalid schedule time: {slot.time}")


