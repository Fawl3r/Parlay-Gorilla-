"""
Autonomous Alpha Engine: self-discovering, self-evolving predictive intelligence.

- Feature discovery: candidate predictive features (odds velocity, CLV momentum, etc.)
- Backtest: rolling historical simulation, IC, p-value, ROI delta
- Validation gate: promote only statistically valid features
- Model augmentation: validated alpha as additional inputs (capped weight)
- Experimentation: A/B tests before production promotion
- Strategy graph: signals as nodes, interaction strength as edges
- Decay monitor: deprecate degrading features
- Meta learning controller: when to retrain, experiment, pause

Imports are safe: missing or broken modules export None; no side effects on import.
"""


def _safe_import(name: str, module_path: str, attr: str):
    """Import attr from module_path; return None on any error (stub)."""
    try:
        mod = __import__(module_path, fromlist=[attr])
        return getattr(mod, attr, None)
    except Exception:
        return None


FeatureDiscoveryEngine = _safe_import("FeatureDiscoveryEngine", "app.alpha.feature_discovery_engine", "FeatureDiscoveryEngine")
BacktestEngine = _safe_import("BacktestEngine", "app.alpha.backtest_engine", "BacktestEngine")
AlphaValidationService = _safe_import("AlphaValidationService", "app.alpha.alpha_validation_service", "AlphaValidationService")
ModelAugmentationService = _safe_import("ModelAugmentationService", "app.alpha.model_augmentation_service", "ModelAugmentationService")
ExperimentationEngine = _safe_import("ExperimentationEngine", "app.alpha.experimentation_engine", "ExperimentationEngine")
StrategyGraphService = _safe_import("StrategyGraphService", "app.alpha.strategy_graph_service", "StrategyGraphService")
AlphaDecayMonitor = _safe_import("AlphaDecayMonitor", "app.alpha.alpha_decay_monitor", "AlphaDecayMonitor")
MetaLearningController = _safe_import("MetaLearningController", "app.alpha.meta_learning_controller", "MetaLearningController")

__all__ = [
    "FeatureDiscoveryEngine",
    "BacktestEngine",
    "AlphaValidationService",
    "ModelAugmentationService",
    "ExperimentationEngine",
    "StrategyGraphService",
    "AlphaDecayMonitor",
    "MetaLearningController",
]
