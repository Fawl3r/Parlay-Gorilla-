from __future__ import annotations

import random
from pathlib import Path

from social_bot.memory_store import BotMemory, MemoryStore, utc_now
from social_bot.post_generator import AnalysisFeedClient, PostType, PostTypeDecider, PostValidator


def test_analysis_feed_parse_minimal() -> None:
    payload = {
        "items": [
            {"slug": "nba/game-1", "angle": "Angle", "key_points": ["a", "b"], "risk_note": "Risk"},
            {"slug": "", "angle": "skip"},
        ]
    }
    items = AnalysisFeedClient._parse_payload(payload, limit=10)
    assert len(items) == 1
    assert items[0].slug == "nba/game-1"


def test_analysis_feed_parse_start_time_optional() -> None:
    payload = {
        "items": [
            {
                "slug": "nfl/game-1",
                "angle": "Angle",
                "key_points": ["a"],
                "start_time": "2026-01-07T18:00:00Z",
                "home_team": "Home",
                "away_team": "Away",
                "matchup": "Away @ Home",
                "league": "NFL",
            }
        ]
    }
    items = AnalysisFeedClient._parse_payload(payload, limit=10)
    assert len(items) == 1
    assert items[0].start_time is not None
    assert items[0].home_team == "Home"
    assert items[0].away_team == "Away"
    assert items[0].matchup == "Away @ Home"
    assert items[0].league == "NFL"


def test_post_type_decider_force(tmp_path: Path) -> None:
    cfg = type(
        "Cfg",
        (),
        {
            "humor_target_ratio": 0.22,
            "include_link_probability": 0.5,
        },
    )()
    store = MemoryStore(path=tmp_path / "memory.json", timezone_name="UTC")
    decider = PostTypeDecider(cfg=cfg, store=store)  # type: ignore[arg-type]

    mem = BotMemory.empty()
    plan = decider.choose(memory=mem, rng=random.Random(1), now=utc_now(), force=PostType.PARLAY_MATH)
    assert plan.post_type == PostType.PARLAY_MATH


def test_validator_rejects_hashtags_and_banned_words() -> None:
    v = PostValidator()
    bad = "This is a lock #parlay"
    res = v.validate(text=bad, post_type=PostType.EDGE_EXPLAINER)
    assert res.ok is False
    assert any(e.startswith("banned_phrase:lock") for e in res.errors)
    assert "hashtags_not_allowed" in res.errors


def test_validator_example_parlay_enforces_reason_risk_bail_and_humor_line() -> None:
    v = PostValidator()
    humor = "Parlays don’t care how confident you feel."
    good = (
        "2-leg example:\n"
        "• Rams ML (trenches edge)\n"
        "• Under (pace control)\n"
        "Confidence: 66/100\n"
        "Risk: backdoor cover\n"
        "Bail if injury status changes.\n"
        f"{humor}"
    )
    res = v.validate(text=good, post_type=PostType.EXAMPLE_PARLAY, required_humor_line=humor)
    assert res.ok is True

    missing_reason = (
        "2-leg example:\n"
        "• Rams ML\n"
        "• Under (pace control)\n"
        "Confidence: 66/100\n"
        "Risk: backdoor cover\n"
        "Bail if injury status changes.\n"
        f"{humor}"
    )
    res2 = v.validate(text=missing_reason, post_type=PostType.EXAMPLE_PARLAY, required_humor_line=humor)
    assert res2.ok is False
    assert "missing_reason_tag" in res2.errors or "bad_leg_count" in res2.errors


