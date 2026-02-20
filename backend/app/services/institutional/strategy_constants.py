"""
Strategy names and default weights for ensemble decomposition.

All strategy outputs are in [0, 1]. Final probability = sum(weight_i * strategy_output_i).
Initial weights equalized; updated by RL optimizer.
"""

# Canonical strategy names (must match DB and RL)
STRATEGY_BASE_MODEL = "base_model_probability"
STRATEGY_CALIBRATION = "calibration_adjustment"
STRATEGY_CLV = "clv_signal"
STRATEGY_MARKET_DISAGREEMENT = "market_disagreement_signal"
STRATEGY_HISTORICAL_ACCURACY = "historical_accuracy_signal"
STRATEGY_VOLATILITY = "volatility_signal"

ALL_STRATEGIES = [
    STRATEGY_BASE_MODEL,
    STRATEGY_CALIBRATION,
    STRATEGY_CLV,
    STRATEGY_MARKET_DISAGREEMENT,
    STRATEGY_HISTORICAL_ACCURACY,
    STRATEGY_VOLATILITY,
]

def default_equal_weights() -> dict[str, float]:
    n = len(ALL_STRATEGIES)
    return {s: 1.0 / n for s in ALL_STRATEGIES}
