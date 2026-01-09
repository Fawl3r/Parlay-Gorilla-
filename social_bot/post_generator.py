from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import httpx

from social_bot.config import BotConfig
from social_bot.memory_store import BotMemory, MemoryStore, utc_now


class PostType(str, Enum):
    EDGE_EXPLAINER = "edge_explainer"
    TRAP_ALERT = "trap_alert"
    EXAMPLE_PARLAY = "example_parlay"
    PARLAY_MATH = "parlay_math"


@dataclass(frozen=True)
class AnalysisItem:
    slug: str
    angle: str
    key_points: list[str]
    risk_note: Optional[str]
    league: Optional[str] = None
    matchup: Optional[str] = None
    home_team: Optional[str] = None
    away_team: Optional[str] = None
    start_time: Optional[datetime] = None


@dataclass(frozen=True)
class PostPlan:
    post_type: PostType
    analysis_items: list[AnalysisItem]
    include_link: bool
    humor_allowed: bool
    humor_line: Optional[str] = None
    humor_line: Optional[str] = None


@dataclass(frozen=True)
class GeneratedPost:
    post_type: PostType
    text: str
    analysis_slug: Optional[str]
    humor_allowed: bool


class HumorPolicy:
    def __init__(self, *, target_ratio: float, window: int = 20) -> None:
        self._target = float(target_ratio)
        self._window = int(window)

    def allow(self, memory: BotMemory, store: MemoryStore) -> bool:
        ratio = store.humor_ratio_recent(memory, window=self._window)
        return ratio < self._target


class PostTypeDecider:
    def __init__(self, *, cfg: BotConfig, store: MemoryStore) -> None:
        self._cfg = cfg
        self._store = store
        self._humor = HumorPolicy(target_ratio=cfg.humor_target_ratio)

    def choose(self, *, memory: BotMemory, rng: random.Random, now: datetime, force: Optional[PostType] = None) -> PostPlan:
        humor_allowed = self._humor.allow(memory, self._store)
        if force is not None:
            return PostPlan(post_type=force, analysis_items=[], include_link=False, humor_allowed=humor_allowed)

        # Weighted selection. Edge explainer is the “most important”.
        weights: list[tuple[PostType, float]] = [
            (PostType.EDGE_EXPLAINER, 0.40),
            (PostType.TRAP_ALERT, 0.25),
            (PostType.PARLAY_MATH, 0.25),
            (PostType.EXAMPLE_PARLAY, 0.10),
        ]
        choice = self._weighted_pick(rng, weights)

        include_link = rng.random() < float(self._cfg.include_link_probability)
        return PostPlan(post_type=choice, analysis_items=[], include_link=include_link, humor_allowed=humor_allowed)

    @staticmethod
    def _weighted_pick(rng: random.Random, weights: list[tuple[PostType, float]]) -> PostType:
        total = sum(max(0.0, float(w)) for _, w in weights)
        roll = rng.random() * (total or 1.0)
        acc = 0.0
        for t, w in weights:
            acc += max(0.0, float(w))
            if roll <= acc:
                return t
        return weights[0][0]


class AnalysisFeedClient:
    def __init__(self, *, url: str, timeout_seconds: float = 10.0) -> None:
        self._url = str(url or "").strip()
        self._timeout = float(timeout_seconds)

    def fetch(self, *, limit: int = 50) -> list[AnalysisItem]:
        if not self._url:
            return []
        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.get(self._url)
            resp.raise_for_status()
            payload = resp.json()
        except Exception:
            return []
        return self._parse_payload(payload, limit=limit)

    @staticmethod
    def _parse_payload(payload: Any, *, limit: int) -> list[AnalysisItem]:
        items_raw = payload.get("items") if isinstance(payload, dict) else None
        if not isinstance(items_raw, list):
            return []
        out: list[AnalysisItem] = []
        for raw in items_raw[: int(limit)]:
            if not isinstance(raw, dict):
                continue
            slug = str(raw.get("slug") or "").strip().lstrip("/")
            if not slug:
                continue
            angle = str(raw.get("angle") or "").strip()
            key_points_raw = raw.get("key_points") or []
            key_points = [str(x).strip() for x in key_points_raw if str(x).strip()] if isinstance(key_points_raw, list) else []
            risk_note = str(raw.get("risk_note") or "").strip() or None
            league = str(raw.get("league") or "").strip() or None
            matchup = str(raw.get("matchup") or "").strip() or None
            home_team = str(raw.get("home_team") or "").strip() or None
            away_team = str(raw.get("away_team") or "").strip() or None
            start_time = _parse_iso8601_optional(raw.get("start_time"))
            out.append(
                AnalysisItem(
                    slug=slug,
                    angle=angle,
                    key_points=key_points[:5],
                    risk_note=risk_note,
                    league=league,
                    matchup=matchup,
                    home_team=home_team,
                    away_team=away_team,
                    start_time=start_time,
                )
            )
        return out


def _parse_iso8601_optional(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


class LinkBuilder:
    def __init__(self, *, frontend_url: str) -> None:
        self._base = str(frontend_url or "https://www.parlaygorilla.com").rstrip("/")

    def analysis_link(self, *, slug: str, post_type: PostType) -> str:
        slug_norm = (slug or "").strip().lstrip("/")
        url = f"{self._base}/analysis/{slug_norm}"
        qs = {
            "utm_source": "x",
            "utm_medium": "social",
            "utm_campaign": "pg_social_bot",
            "utm_content": str(post_type.value),
        }
        return self._merge_query(url, qs)

    @staticmethod
    def _merge_query(url: str, new_params: dict[str, str]) -> str:
        parsed = urlparse(url)
        existing = dict(parse_qsl(parsed.query, keep_blank_values=True))
        existing.update({k: v for k, v in new_params.items() if v})
        query = urlencode(existing, doseq=True)
        return urlunparse(parsed._replace(query=query))


SYSTEM_PROMPT = """You are Parlay Gorilla on X.

VOICE IDENTITY: Write like a real bettor talking to another bettor.
Tone = confident, blunt, educational, slightly humorous.
Never sound corporate, promotional, or generic.

Think:
- "This is how tickets actually die."
- "I've seen this mistake too many times."

REQUIRED STRUCTURE (EVERY POST):
- 4–6 lines total
- Short lines (no paragraphs)
- Natural pauses using line breaks
- Final line may include a soft CTA

OPENING RULE: The first line must be a DIRECT STATEMENT, not advice.
✅ Good: "Most parlays fail because…" / "Parlays don't lose because of bad luck." / "If you're not checking matchups…"
❌ Never start with: "Consider…" / "It's important to…" / "Understanding that…"

CONTENT RULES: Each post must include at least ONE of:
- A real betting concept (form, injuries, tempo, matchups, game script)
- A real risk (backdoor cover, late scratch, garbage time)
- A real mistake bettors make (skipping homework, betting vibes)

HUMOR RULES:
- Light, dry, self-aware
- Max 1 humorous line
- Never meme-y or goofy
- Allowed: "not vibes" / "skip the homework" / "that's where tickets die"

CTA RULES:
- Include a growth CTA in all posts (end of post)
- Natural, not corporate or hype
- Examples: 
  - "Like and share if this helps. 🦍"
  - "Share this. Gorilla's strong together. 🦍"
  - "Like and share. 🦍"
  - "🦍 Check out our analysis at www.ParlayGorilla.com 🦍"
- Can also include analysis link if context available

BANNED WORDS: lock, guaranteed, free money, smash, hammer, significantly, for deeper insights, consider, understand

EMOJI RULE: Max 2 emojis (for CTA format like "🦍 Check out our analysis at www.ParlayGorilla.com 🦍"), 🦍 only, optional

TARGET LENGTH: 180–260 characters. Never exceed 280.

CRITICAL: Maximum 280 characters total (X's limit). Count carefully.
No hashtags. Never mention sportsbooks.
"""


class PromptBuilder:
    def __init__(self, *, link_builder: LinkBuilder) -> None:
        self._links = link_builder

    def build(self, *, plan: PostPlan) -> tuple[str, str]:
        system = SYSTEM_PROMPT.strip()
        user = self._user_prompt(plan)
        return system, user

    def _user_prompt(self, plan: PostPlan) -> str:
        parts: list[str] = []
        parts.append("Write ONE X post (single post). Output ONLY the post text (no quotes, no JSON).")
        parts.append("")
        parts.append("STRUCTURE REQUIREMENTS:")
        parts.append("- 4–6 lines total")
        parts.append("- Short lines (no paragraphs)")
        parts.append("- Natural pauses using line breaks")
        parts.append("- First line MUST be a direct statement (not advice)")
        parts.append("")
        parts.append("LENGTH: Target 180–260 characters. NEVER exceed 280. Count every character.")
        parts.append("")
        if plan.humor_line:
            parts.append("MANDATORY: Include this exact line verbatim ONCE (no quotes):")
            parts.append(plan.humor_line)
        elif plan.humor_allowed:
            parts.append("Humor allowed: Light, dry, self-aware. Max 1 humorous line.")
        else:
            parts.append("Do NOT use humor in this post.")
        parts.append("")
        parts.append("MANDATORY: End with a growth CTA (natural, not corporate):")
        parts.append('Examples: "Like and share if this helps. 🦍" / "Share this. Gorilla\'s strong together. 🦍" / "Like and share. 🦍" / "🦍 Check out our analysis at www.ParlayGorilla.com 🦍"')
        if plan.include_link:
            parts.append("You can also include analysis link if context is provided below.")
        parts.append("")
        parts.append(f"Post type: {self._label(plan.post_type)}")
        parts.append(self._type_rules(plan))
        return "\n".join(parts).strip()

    def _type_rules(self, plan: PostPlan) -> str:
        t = plan.post_type
        if t == PostType.EDGE_EXPLAINER:
            return self._edge_explainer(plan)
        if t == PostType.TRAP_ALERT:
            return self._trap_alert(plan)
        if t == PostType.EXAMPLE_PARLAY:
            return self._example_parlay(plan)
        return self._parlay_math(plan)

    def _edge_explainer(self, plan: PostPlan) -> str:
        lines = [
            "Explain a real betting concept or edge.",
            "Must include at least ONE of: form, injuries, tempo, matchups, game script.",
            "First line must be a direct statement (not advice).",
            "Example opening: 'Most parlays fail because…' or 'If you're not checking matchups…'",
            "Keep it educational and practical.",
        ]
        return self._with_context(lines, plan)

    def _trap_alert(self, plan: PostPlan) -> str:
        lines = [
            "Alert about a real risk or common mistake.",
            "Must mention a specific risk: backdoor cover, late scratch, garbage time, turnovers, pace flip, weather swing.",
            "First line must be a direct statement (not advice).",
            "Example opening: 'Parlays don't lose because of bad luck.' or 'That's where tickets die.'",
            "Keep it practical and non-hype.",
        ]
        return self._with_context(lines, plan)

    def _example_parlay(self, plan: PostPlan) -> str:
        lines = [
            "Write a 2-leg example ticket (not picks-as-a-service).",
            "MANDATORY RULES:",
            "- Exactly 2 legs (no 3rd leg).",
            "- Each leg MUST include a short reason tag in parentheses (2–5 words).",
            "- Use generic markets only: ML / spread / total (NO exact numbers).",
            "- Risk must be specific (pick ONE): backdoor cover, turnovers, pace flip, late scratch, weather swing, garbage-time points.",
            "- Include a bail condition line that starts with: Bail",
            "- Must include:",
            "  - Confidence: NN/100",
            "  - Risk: ...",
            "Tone: like texting betting friends. No 'hypothetical' / no 'structure' wording.",
            "Format example:",
            "2-leg example:",
            "• Team ML (trenches edge)",
            "• Under (pace control)",
            "Confidence: 66/100",
            "Risk: backdoor cover",
            "Bail if injury status changes.",
        ]
        return self._with_context(lines, plan)

    def _parlay_math(self, plan: PostPlan) -> str:
        lines = [
            "Teach one clear parlay math or bankroll concept in plain English.",
            "First line must be a direct statement (not advice).",
            "Example opening: 'Parlays don't care how confident you feel.' or 'The math is rude, but it's honest.'",
            "Keep it short and useful. No picks. No hype.",
        ]
        return self._with_context(lines, plan)

    def _with_context(self, lines: list[str], plan: PostPlan) -> str:
        out = list(lines)
        if plan.analysis_items:
            out.append("")
            out.append("Use this matchup context (only what helps):")
            for it in plan.analysis_items[:3]:
                out.append(f"- slug: {it.slug}")
                out.append(f"  angle: {it.angle[:240]}")
                if it.key_points:
                    out.append(f"  key_points: {', '.join(it.key_points[:3])}")
                if it.risk_note:
                    out.append(f"  risk_note: {it.risk_note[:180]}")
                if plan.include_link:
                    out.append(f"  analysis_link: {self._links.analysis_link(slug=it.slug, post_type=plan.post_type)}")
        return "\n".join(out).strip()

    @staticmethod
    def _label(post_type: PostType) -> str:
        return {
            PostType.EDGE_EXPLAINER: "Edge Explainer",
            PostType.TRAP_ALERT: "Trap Alert",
            PostType.EXAMPLE_PARLAY: "Example 2–3 Leg Parlay Structure (Hypothetical)",
            PostType.PARLAY_MATH: "Parlay Math / Bankroll Education",
        }[post_type]


class OpenAiPostWriter:
    def __init__(self, *, api_key: str, base_url: str, model: str, timeout_seconds: float) -> None:
        self._api_key = str(api_key or "").strip()
        self._base_url = str(base_url or "https://api.openai.com/v1").rstrip("/")
        self._model = str(model or "gpt-4o-mini").strip()
        self._timeout = float(timeout_seconds)

    def write(self, *, system_prompt: str, user_prompt: str) -> str:
        url = f"{self._base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}
        body = {
            "model": self._model,
            "temperature": 0.7,
            "max_tokens": 100,  # Allow for 4-6 lines, 180-260 characters
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.post(url, headers=headers, content=json.dumps(body).encode("utf-8"))
        resp.raise_for_status()
        payload = resp.json() or {}
        choices = payload.get("choices") or []
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("OpenAI returned no choices")
        msg = choices[0].get("message") if isinstance(choices[0], dict) else None
        text = (msg or {}).get("content") if isinstance(msg, dict) else None
        return str(text or "").strip()


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: list[str]


class PostValidator:
    _emoji_re = re.compile(r"[\U0001F300-\U0001FAFF\U00002700-\U000027BF\U0001F1E6-\U0001F1FF]")

    def __init__(self) -> None:
        self._banned_phrases = [
            "lock",
            "guarantee",
            "guaranteed",
            "free money",
            "can't lose",
            "cannot lose",
            "sure thing",
            "no brainer",
            "smash",
            "hammer",
            "significantly",
            "for deeper insights",
            "consider",
            "understand",
        ]
        self._sportsbooks = [
            "draftkings",
            "fanduel",
            "betmgm",
            "caesars",
            "pointsbet",
            "bet365",
            "barstool",
            "sportsbook",
        ]

    def validate(self, *, text: str, post_type: PostType, required_humor_line: Optional[str] = None) -> ValidationResult:
        errors: list[str] = []
        cleaned = str(text or "").strip()
        if not cleaned:
            errors.append("empty")
            return ValidationResult(ok=False, errors=errors)

        if len(cleaned) > 280:
            errors.append("too_long")
        if len(cleaned) < 180:
            errors.append("too_short")
        if "#" in cleaned:
            errors.append("hashtags_not_allowed")

        # Check structure: should have 4-6 lines
        lines = [ln.strip() for ln in cleaned.split("\n") if ln.strip()]
        if len(lines) < 4:
            errors.append(f"too_few_lines:{len(lines)}")
        if len(lines) > 6:
            errors.append(f"too_many_lines:{len(lines)}")
        
        # Check opening rule: first line must be a direct statement, not advice
        if lines:
            first_line = lines[0].lower()
            bad_starts = ["consider", "it's important to", "understanding that", "you should", "remember to", "make sure to"]
            if any(first_line.startswith(bad) for bad in bad_starts):
                errors.append("bad_opening_advice")

        lowered = cleaned.lower()
        for phrase in self._banned_phrases:
            if phrase in lowered:
                errors.append(f"banned_phrase:{phrase}")
        for name in self._sportsbooks:
            if name in lowered:
                errors.append(f"sportsbook_mention:{name}")

        emoji_count = len(self._emoji_re.findall(cleaned))
        if emoji_count > 2:  # Allow up to 2 emojis for CTA format (🦍 ... 🦍)
            errors.append("too_many_emojis")
        
        # Check for growth CTA (mandatory in all posts)
        cta_phrases = ["like and share", "share this", "gorilla's strong", "gorillas strong", "check out our analysis", "parlaygorilla.com"]
        has_cta = any(phrase in lowered for phrase in cta_phrases)
        if not has_cta:
            errors.append("missing_growth_cta")

        if required_humor_line:
            if required_humor_line not in cleaned:
                errors.append("missing_required_humor_line")

        if post_type == PostType.EXAMPLE_PARLAY:
            if "confidence:" not in lowered:
                errors.append("missing_confidence")
            if "risk:" not in lowered:
                errors.append("missing_risk_note")
            if "bail" not in lowered:
                errors.append("missing_bail_condition")

            # Exactly 2 legs required, each with a short reason tag in parentheses.
            leg_lines = [ln.strip() for ln in cleaned.splitlines() if ln.strip().startswith("•")]
            if len(leg_lines) != 2:
                errors.append(f"bad_leg_count:{len(leg_lines)}")
            for ln in leg_lines:
                m = re.search(r"\(([^)]+)\)", ln)
                if not m:
                    errors.append("missing_reason_tag")
                    continue
                tag = m.group(1).strip()
                words = [w for w in re.split(r"\s+", tag) if w]
                if not (2 <= len(words) <= 5):
                    errors.append("bad_reason_tag_word_count")

            # Risk must be specific (no generic platitudes).
            risk_allowed = [
                "backdoor",
                "turnover",
                "turnovers",
                "pace flip",
                "late scratch",
                "weather swing",
                "garbage-time",
                "garbage time",
            ]
            if "risk:" in lowered and not any(k in lowered for k in risk_allowed):
                errors.append("risk_not_specific")

        return ValidationResult(ok=not errors, errors=errors)


class PostGenerator:
    def __init__(
        self,
        *,
        cfg: BotConfig,
        store: MemoryStore,
        feed: AnalysisFeedClient,
        prompt_builder: PromptBuilder,
        writer: OpenAiPostWriter,
        validator: PostValidator,
    ) -> None:
        self._cfg = cfg
        self._store = store
        self._feed = feed
        self._prompts = prompt_builder
        self._writer = writer
        self._validator = validator

    def build_plan(self, *, base: PostPlan, memory: BotMemory, rng: random.Random, now: datetime) -> PostPlan:
        if base.post_type in {PostType.TRAP_ALERT, PostType.EXAMPLE_PARLAY} or base.include_link:
            items = self._select_analysis_items(post_type=base.post_type, memory=memory, rng=rng, now=now)
            if base.post_type in {PostType.TRAP_ALERT, PostType.EXAMPLE_PARLAY} and not items:
                # If we can't get matchup context, fall back to a non-feed type.
                fallback = PostType.PARLAY_MATH if base.post_type == PostType.EXAMPLE_PARLAY else PostType.EDGE_EXPLAINER
                return PostPlan(post_type=fallback, analysis_items=[], include_link=False, humor_allowed=base.humor_allowed, humor_line=None)
            humor_line = self._pick_analysis_humor_line(memory=memory, rng=rng) if items else None
            return PostPlan(
                post_type=base.post_type,
                analysis_items=items,
                include_link=base.include_link and bool(items),
                humor_allowed=(base.humor_allowed or bool(humor_line)),
                humor_line=humor_line,
            )
        return base

    @staticmethod
    def _analysis_humor_bank() -> list[str]:
        # Subtle, credible, lightly funny + educational one-liners (no emojis, no hype).
        return [
            "Parlays don’t care how confident you feel.",
            "The math is rude, but it’s honest.",
            "Looks clean. Which makes me nervous.",
            "This is where discipline usually leaves the group chat.",
            "Variance loves your ‘easy’ leg.",
            "If you can’t explain the edge fast, don’t stack it.",
        ]

    def _pick_analysis_humor_line(self, *, memory: BotMemory, rng: random.Random) -> str:
        recent = " ".join(self._store.recent_texts(memory, limit=40)).lower()
        bank = [x for x in self._analysis_humor_bank() if x.lower() not in recent]
        if not bank:
            bank = self._analysis_humor_bank()
        return bank[int(rng.random() * len(bank))]

    def generate(self, *, plan: PostPlan, max_attempts: int = 4) -> GeneratedPost:
        now = utc_now()
        system, user = self._prompts.build(plan=plan)

        last_errors: list[str] = []
        for attempt in range(int(max_attempts)):
            draft = self._writer.write(system_prompt=system, user_prompt=self._with_feedback(user, last_errors))
            draft = self._normalize_output(draft)
            check = self._validator.validate(text=draft, post_type=plan.post_type, required_humor_line=plan.humor_line)
            if check.ok:
                slug = plan.analysis_items[0].slug if plan.analysis_items else None
                return GeneratedPost(post_type=plan.post_type, text=draft, analysis_slug=slug, humor_allowed=plan.humor_allowed)
            # Log the attempt and length for debugging (using print since PostGenerator doesn't have logger)
            print(f"⚠️  Attempt {attempt + 1}/{max_attempts}: Generated {len(draft)} chars (limit: 280), errors: {check.errors}")
            last_errors = check.errors

        raise RuntimeError(f"Failed to generate a compliant post: {', '.join(last_errors[:6])}")

    @staticmethod
    def _with_feedback(user_prompt: str, errors: list[str]) -> str:
        if not errors:
            return user_prompt
        lines = [user_prompt, "", "Rewrite to fix these issues:"]
        for e in errors[:8]:
            if e == "too_long":
                lines.append("- Post is too long. You MUST keep it under 280 characters total. Shorten immediately by removing unnecessary words.")
            elif e == "too_short":
                lines.append("- Post is too short. Target 180-260 characters. Add more substance.")
            elif e.startswith("too_few_lines"):
                lines.append("- Post needs 4-6 lines. Add more lines with natural breaks.")
            elif e.startswith("too_many_lines"):
                lines.append("- Post has too many lines. Keep it to 4-6 lines maximum.")
            elif e == "bad_opening_advice":
                lines.append("- First line must be a DIRECT STATEMENT, not advice. Start with facts like 'Most parlays fail because...' or 'Parlays don't lose because...' NOT 'Consider...' or 'You should...'")
            elif e == "missing_growth_cta":
                lines.append("- MANDATORY: End with a growth CTA. Examples: 'Like and share if this helps. 🦍' / 'Share this. Gorilla's strong together. 🦍' / 'Like and share. 🦍' / '🦍 Check out our analysis at www.ParlayGorilla.com 🦍'")
            elif e.startswith("banned_phrase"):
                lines.append(f"- Banned phrase detected: {e.split(':')[1] if ':' in e else e}. Remove it.")
            else:
                lines.append(f"- {e}")
        return "\n".join(lines).strip()

    @staticmethod
    def _normalize_output(text: str) -> str:
        cleaned = str(text or "").strip()
        if cleaned.startswith('\"') and cleaned.endswith('\"') and len(cleaned) >= 2:
            cleaned = cleaned[1:-1].strip()
        return cleaned

    def _select_analysis_items(self, *, post_type: PostType, memory: BotMemory, rng: random.Random, now: datetime) -> list[AnalysisItem]:
        items = self._feed.fetch(limit=60)
        if not items:
            return []

        # Only pick matchups that start soon. If the feed doesn't include start_time yet,
        # we keep backward compatibility and skip this filter.
        if any(it.start_time is not None for it in items):
            window_end = now + timedelta(hours=int(self._cfg.analysis_upcoming_window_hours))
            items = [it for it in items if it.start_time is not None and now <= it.start_time <= window_end]

        needed = 2 if post_type == PostType.EXAMPLE_PARLAY else 1
        chosen: list[AnalysisItem] = []
        for it in items:
            if self._store.slug_used_within_hours(memory, slug=it.slug, hours=self._cfg.analysis_slug_reuse_cooldown_hours, now=now):
                continue
            if any(x.slug == it.slug for x in chosen):
                continue
            chosen.append(it)
            if len(chosen) >= needed:
                break
        return chosen


def build_default_post_generator(*, cfg: BotConfig, store: MemoryStore) -> tuple[PostTypeDecider, PostGenerator]:
    decider = PostTypeDecider(cfg=cfg, store=store)
    feed = AnalysisFeedClient(url=cfg.analysis_feed_url, timeout_seconds=12.0)
    links = LinkBuilder(frontend_url=cfg.frontend_url)
    prompts = PromptBuilder(link_builder=links)
    writer = OpenAiPostWriter(
        api_key=cfg.openai_api_key,
        base_url=cfg.openai_base_url,
        model=cfg.openai_model,
        timeout_seconds=cfg.openai_timeout_seconds,
    )
    validator = PostValidator()
    generator = PostGenerator(cfg=cfg, store=store, feed=feed, prompt_builder=prompts, writer=writer, validator=validator)
    return decider, generator


