from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from random import Random
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlencode

from src.site_feed import SiteFeedClient
from src.settings import Settings


@dataclass(frozen=True)
class AppFeature:
    headline: str
    benefit: str
    path: str
    campaign: str


_CTA_LEADS = [
    "Angles:",
    "Matchup hub:",
    "Build here:",
    "Quick link:",
    "Try it:",
]

_TIPS = [
    "Shop the number before you shop the narrative.",
    "If the price moved, ask why it moved.",
    "Don’t scale your stake to your confidence — scale it to your edge.",
    "Avoid chasing. The next bet isn’t owed to you.",
    "Track results by market + price, not by vibes.",
    "If you can’t write the edge in one sentence, pass.",
    "Correlation is not the same thing as 'I like both'.",
    "When you feel rushed, you’re usually forcing it.",
    "Great bets at bad numbers are still bad bets.",
    "Stick to a unit size and protect the bankroll.",
    "A half-point is real money over a season.",
    "If you need a miracle, you sized it wrong.",
    "Respect uncertainty: variance is the whole game.",
    "Prefer simple, repeatable edges over hot takes.",
    "Before you bet: injuries, number, and schedule spot.",
    "Don’t turn a single opinion into a 6-leg lottery ticket.",
    "If the edge is small, reduce the stake — don’t add legs.",
    "You don’t need action on every game. You need good numbers.",
    "If you’re tilted, you’re not thinking in probabilities.",
    "A parlay is a product. The inputs matter more than the story.",
    "One bad leg breaks the ticket. Prioritize leg quality.",
    "Know your limits: if it’s confusing, it’s usually -EV.",
    "Price discipline beats prediction skill long-term.",
    "Try writing your bet in one sentence. If it’s messy, pass.",
    "Don’t confuse a close game with a good bet.",
    "Bankroll management is the edge you control.",
    "Avoid adding legs just to chase a bigger payout.",
    "If you’re relying on 'they want it more', you’re guessing.",
    "Short streaks mean nothing. Process does.",
    "Don’t anchor on opening lines. Re-evaluate with new info.",
]

_QUESTIONS = [
    "If you’re building a 3-leg parlay today, what market is your anchor — ML, spread, or total?",
    "Would you rather have a great read at a bad number, or a decent read at a great number?",
    "What’s one betting rule you wish you followed earlier?",
    "Do you prefer early numbers or closing line? Why?",
    "What’s your #1 filter before you add a leg to a parlay?",
    "What’s the cleanest edge you look for: matchup, injury news, or market move?",
    "When do you pass on a bet even if you like the side?",
    "What’s your go-to parlay structure: 2-leg, 3-leg, or 4+?",
    "Do you set a daily limit on plays? What is it?",
    "Do you treat parlays as entertainment or as a serious strategy?",
    "What’s one stat you think the public overweights?",
    "If you could only bet one market for a month, which is it?",
    "What’s your biggest leak: sizing, discipline, or price?",
]

_WATCH_POINTS = [
    "Watch pace + turnover battle — that’s where the hidden possessions live.",
    "Key question: can the underdog keep it close early, or does it snowball?",
    "Look for mismatch leverage (trenches, boards, or special teams).",
    "The number matters: the same side is a bet at one price and a pass at another.",
    "Market note: movement without news is usually just liquidity + timing.",
    "If the favorite starts slow, in-game may offer a better entry than pregame.",
    "Watch foul trouble / penalty count — it changes the game script fast.",
    "If one side relies on explosive plays, variance is higher than the box score shows.",
    "If the matchup is a style clash, tempo is the swing factor.",
    "If the total is tight, late-game pace matters (timeouts, fouls, clock).",
]

_MATCHUP_QUESTIONS = [
    "What’s your lean on this one at the current number?",
    "If the line moves 1 point, does your bet change?",
    "Would you rather play it pregame or look for an in-game entry?",
    "Would you bet it solo, or only as a parlay leg?",
    "Which matters more here: matchup edge or number edge?",
]

_FEATURES: List[AppFeature] = [
    AppFeature(
        headline="Want a decision-first matchup angle before you bet?",
        benefit="Browse the slate and open any game for a short, readable breakdown.",
        path="/analysis",
        campaign="analysis_hub",
    ),
    AppFeature(
        headline="Need a quick parlay idea (without overthinking it)?",
        benefit="Use the public AI builder to generate a starting point in under a minute.",
        path="/build",
        campaign="build",
    ),
    AppFeature(
        headline="New to Parlay Gorilla?",
        benefit="The tutorial walks through the flow step-by-step so you can get value fast.",
        path="/tutorial",
        campaign="tutorial",
    ),
]


class DynamicContextBuilder:
    def __init__(self, *, settings: Settings, site_feed: SiteFeedClient) -> None:
        self._settings = settings
        self._site_feed = site_feed

    def build(self, *, rng: Random, now: datetime, posted_raw: List[dict]) -> Dict[str, str]:
        variant = self._pick_variant(rng)
        frontend = (self._settings.site_content.frontend_url or "").strip().rstrip("/")

        analysis_hub_url = self._frontend_url(frontend, "/analysis", campaign="analysis_hub", variant=variant)
        build_url = self._frontend_url(frontend, "/build", campaign="build", variant=variant)
        tutorial_url = self._frontend_url(frontend, "/tutorial", campaign="tutorial", variant=variant)
        docs_url = self._frontend_url(frontend, "/docs", campaign="docs", variant=variant)
        pricing_url = self._frontend_url(frontend, "/pricing", campaign="pricing", variant=variant)
        app_url = self._frontend_url(frontend, "/app", campaign="app", variant=variant)

        matchup, analysis_url = self._matchup_link(rng=rng, now=now, posted_raw=posted_raw, fallback_url=analysis_hub_url)

        tips = self._pick_distinct(rng, _TIPS, count=3)
        feature = rng.choice(_FEATURES)

        return {
            "cta_lead": rng.choice(_CTA_LEADS),
            "question": rng.choice(_QUESTIONS),
            "tip": rng.choice(_TIPS),
            "tip1": tips[0],
            "tip2": tips[1],
            "tip3": tips[2],
            "watch_point": rng.choice(_WATCH_POINTS),
            "matchup_question": rng.choice(_MATCHUP_QUESTIONS),
            "matchup": matchup,
            "analysis_url": analysis_url,
            "analysis_hub_url": analysis_hub_url,
            "build_url": build_url,
            "tutorial_url": tutorial_url,
            "docs_url": docs_url,
            "pricing_url": pricing_url,
            "app_url": app_url,
            "feature_headline": feature.headline,
            "feature_benefit": feature.benefit,
            "feature_url": self._frontend_url(frontend, feature.path, campaign=feature.campaign, variant=variant),
        }

    def _pick_variant(self, rng: Random) -> str:
        variants = [v for v in self._settings.site_content.ab_variants if str(v).strip()] or ["a", "b"]
        return str(rng.choice(variants)).strip()

    def _frontend_url(self, base: str, path: str, *, campaign: str, variant: str) -> str:
        if not base:
            # Keep output usable even if not configured.
            return path
        query = urlencode(
            {
                "utm_source": "x",
                "utm_medium": "social",
                "utm_campaign": campaign,
                "utm_content": f"variant_{variant}",
            }
        )
        p = (path or "").strip()
        if not p.startswith("/"):
            p = "/" + p
        return f"{base}{p}?{query}"

    def _matchup_link(self, *, rng: Random, now: datetime, posted_raw: List[dict], fallback_url: str) -> Tuple[str, str]:
        upcoming = self._site_feed.get_upcoming_matchup_link(now=now, posted_raw=posted_raw)
        if upcoming is None:
            return "Today’s slate", fallback_url
        matchup, url, _slug = upcoming
        return matchup, url

    def _pick_distinct(self, rng: Random, pool: List[str], *, count: int) -> List[str]:
        if not pool:
            return [""] * count
        picked: List[str] = []
        available = list(pool)
        rng.shuffle(available)
        for _ in range(count):
            if not available:
                available = list(pool)
                rng.shuffle(available)
            picked.append(available.pop())
        return picked


