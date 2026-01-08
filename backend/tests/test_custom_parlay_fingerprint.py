from __future__ import annotations

from datetime import datetime, timezone

from app.services.custom_parlay_verification.fingerprint import (
    CustomParlayFingerprintGenerator,
    CustomParlayFingerprintLeg,
)


def test_custom_parlay_fingerprint_is_order_invariant_for_legs():
    gen = CustomParlayFingerprintGenerator(model_version="pg-1.0.0", window_seconds=600)
    now = datetime(2026, 1, 8, 12, 0, 1, tzinfo=timezone.utc)

    legs_a = [
        CustomParlayFingerprintLeg(matchup_id="m2", market_type="h2h", pick="home", odds_snapshot="-110"),
        CustomParlayFingerprintLeg(matchup_id="m1", market_type="totals", pick="over", point=44.5, odds_snapshot="-105"),
    ]
    legs_b = list(reversed(legs_a))

    fp_a = gen.compute(user_id="user-1", legs=legs_a, now_utc=now).parlay_fingerprint
    fp_b = gen.compute(user_id="user-1", legs=legs_b, now_utc=now).parlay_fingerprint

    assert fp_a == fp_b


def test_custom_parlay_fingerprint_changes_when_pick_changes():
    gen = CustomParlayFingerprintGenerator(model_version="pg-1.0.0", window_seconds=600)
    now = datetime(2026, 1, 8, 12, 0, 1, tzinfo=timezone.utc)

    base = [
        CustomParlayFingerprintLeg(matchup_id="m1", market_type="totals", pick="over", point=44.5, odds_snapshot="-110"),
    ]
    changed = [
        CustomParlayFingerprintLeg(matchup_id="m1", market_type="totals", pick="under", point=44.5, odds_snapshot="-110"),
    ]

    fp_a = gen.compute(user_id="user-1", legs=base, now_utc=now).parlay_fingerprint
    fp_b = gen.compute(user_id="user-1", legs=changed, now_utc=now).parlay_fingerprint

    assert fp_a != fp_b


def test_custom_parlay_fingerprint_changes_when_odds_snapshot_changes():
    gen = CustomParlayFingerprintGenerator(model_version="pg-1.0.0", window_seconds=600)
    now = datetime(2026, 1, 8, 12, 0, 1, tzinfo=timezone.utc)

    a = [CustomParlayFingerprintLeg(matchup_id="m1", market_type="h2h", pick="home", odds_snapshot="-110")]
    b = [CustomParlayFingerprintLeg(matchup_id="m1", market_type="h2h", pick="home", odds_snapshot="-120")]

    fp_a = gen.compute(user_id="user-1", legs=a, now_utc=now).parlay_fingerprint
    fp_b = gen.compute(user_id="user-1", legs=b, now_utc=now).parlay_fingerprint
    assert fp_a != fp_b


def test_custom_parlay_fingerprint_changes_across_generation_windows():
    gen = CustomParlayFingerprintGenerator(model_version="pg-1.0.0", window_seconds=600)

    legs = [CustomParlayFingerprintLeg(matchup_id="m1", market_type="h2h", pick="home", odds_snapshot="-110")]
    t1 = datetime(2026, 1, 8, 12, 0, 1, tzinfo=timezone.utc)  # bucket A
    t2 = datetime(2026, 1, 8, 12, 10, 1, tzinfo=timezone.utc)  # bucket B

    fp1 = gen.compute(user_id="user-1", legs=legs, now_utc=t1).parlay_fingerprint
    fp2 = gen.compute(user_id="user-1", legs=legs, now_utc=t2).parlay_fingerprint

    assert fp1 != fp2


