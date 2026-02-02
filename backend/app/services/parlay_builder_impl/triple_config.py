"""
Triple Parlay confidence-gated constants.

STRICT policy: no fallback ladder, no time-window expansion, no market relaxation.
Strong Edge: deterministic gate using existing analysis/model signals (no new data).

IMPORTANT: confidence_score is 0-100 everywhere in this codebase (model_win_probability,
leg selection, candidate_leg_service). If any caller ever switches to 0-1 scale,
Triple strong-edge checks will break silently. We assert 0 <= confidence_score <= 100
where we use it for Triple so a scale change fails fast.
"""

# Confidence threshold (0-100 scale only; see module docstring)
TRIPLE_MIN_CONFIDENCE = 62.0
assert 0 <= TRIPLE_MIN_CONFIDENCE <= 100, "TRIPLE_MIN_CONFIDENCE must be on 0-100 scale"

# Optional EV gate (omit if not computed)
TRIPLE_MIN_EV = 0.0

# Max legs from same game (avoid stacking)
TRIPLE_MAX_SAME_GAME = 1

# Max legs from same team (avoid correlated)
TRIPLE_MAX_SAME_TEAM = 1

# Allowed market types for Triple; each leg must have odds for its own market
TRIPLE_ALLOWED_MARKETS = frozenset({"h2h", "spreads", "totals", "moneyline", "spread", "total"})
