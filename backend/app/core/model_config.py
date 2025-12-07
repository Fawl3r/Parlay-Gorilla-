"""
Model Version Configuration

Single source of truth for model versioning.
Bump this when prediction logic changes to track performance across versions.

Format: pg-{major}.{minor}.{patch}
- major: Breaking changes to prediction logic
- minor: New features or significant weight changes
- patch: Bug fixes, minor tuning
"""

# Current model version
MODEL_VERSION = "pg-1.0.0"

# Version history (for reference)
VERSION_HISTORY = {
    "pg-1.0.0": {
        "date": "2024-12-05",
        "description": "Initial production model with multi-sport engines",
        "changes": [
            "MLB probability engine with pitcher/bullpen weighting",
            "Soccer probability engine with xG integration",
            "Unified feature pipeline from SportsRadar + ESPN",
            "Per-team bias calibration system",
        ],
    },
}

# Weight configurations by sport
# These can be tuned and versioned independently
SPORT_WEIGHTS = {
    "NFL": {
        "odds_weight": 0.50,
        "stats_weight": 0.30,
        "situational_weight": 0.20,
    },
    "NBA": {
        "odds_weight": 0.45,
        "stats_weight": 0.35,
        "situational_weight": 0.20,
    },
    "NHL": {
        "odds_weight": 0.50,
        "stats_weight": 0.30,
        "situational_weight": 0.20,
    },
    "MLB": {
        "odds_weight": 0.40,  # More variance in baseball
        "stats_weight": 0.40,  # Pitcher matchup is huge
        "situational_weight": 0.20,
    },
    "SOCCER": {
        "odds_weight": 0.45,
        "stats_weight": 0.35,
        "situational_weight": 0.20,
    },
}

# Home advantage by sport (fraction to add to home probability)
HOME_ADVANTAGE = {
    "NFL": 0.025,       # 2.5%
    "NBA": 0.035,       # 3.5%
    "NHL": 0.025,       # 2.5%
    "MLB": 0.020,       # 2.0%
    "SOCCER": 0.030,    # 3.0%
    "SOCCER_EPL": 0.030,
    "SOCCER_MLS": 0.025,
}

# Calibration settings
CALIBRATION_CONFIG = {
    "min_games_for_adjustment": 10,  # Min games before applying team bias
    "max_bias_adjustment": 0.05,     # Max +/- 5% adjustment
    "recalibration_frequency_days": 7,  # How often to recalculate
    "lookback_games": 20,            # Games to include in bias calculation
}

# Upset finder thresholds
UPSET_CONFIG = {
    "min_edge_threshold": 0.05,  # 5% edge minimum
    "risk_tier_thresholds": {
        "low": {"min_prob": 0.45, "max_odds": 150},
        "medium": {"min_prob": 0.35, "max_odds": 250},
        "high": {"min_prob": 0.0, "max_odds": 1000},
    },
    "max_upsets_by_parlay_type": {
        "safe": 1,
        "balanced": 3,
        "degen": 6,
    },
}


def get_sport_weights(sport: str) -> dict:
    """Get weight configuration for a sport"""
    sport_key = sport.upper()
    return SPORT_WEIGHTS.get(sport_key, SPORT_WEIGHTS["NFL"])


def get_home_advantage(sport: str) -> float:
    """Get home advantage for a sport"""
    sport_key = sport.upper()
    return HOME_ADVANTAGE.get(sport_key, 0.025)

