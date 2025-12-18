"""Analysis generation pipeline (core + full article).

This package is the production entrypoint for generating AI game analyses.
It is intentionally split into small modules to keep responsibilities clear:
- repository: DB reads/writes + concurrency guards
- core generator: fast, deterministic core analysis (no long OpenAI calls)
- full article generator: long-form article generation (background)
- orchestrator: route-facing coordination and policy decisions
"""

from .analysis_orchestrator import AnalysisOrchestratorService

__all__ = ["AnalysisOrchestratorService"]


