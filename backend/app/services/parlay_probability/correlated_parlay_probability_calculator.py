from __future__ import annotations

import hashlib
from statistics import NormalDist
from typing import Any, Dict, List, Optional

import numpy as np

from app.services.parlay_probability.parlay_correlation_model import ParlayCorrelationModel


class CorrelatedParlayProbabilityCalculator:
    """
    Computes parlay hit probability with correlation-aware handling of same-game legs.

    Strategy:
    - Partition legs by game_id.
    - For groups of size 1: use the marginal probability directly.
    - For groups of size >= 2: estimate P(all hit) via Monte Carlo using a Gaussian copula.
    - Multiply group probabilities across games (assume cross-game independence).

    Determinism:
    - By default, uses a deterministic seed derived from the legs + risk_profile.
    - Callers can override with `rng_seed` for tests.
    """

    _DEFAULT_SAMPLES_BY_PROFILE: Dict[str, int] = {
        # Baseline sample sizes for same-game groups (size 3-4). We scale up/down by group size
        # to balance stability vs latency.
        "conservative": 10000,
        "balanced": 7000,
        "degen": 5000,
    }

    def __init__(
        self,
        correlation_model: ParlayCorrelationModel,
        *,
        samples_by_profile: Optional[Dict[str, int]] = None,
    ):
        self._correlation_model = correlation_model
        self._samples_by_profile = dict(self._DEFAULT_SAMPLES_BY_PROFILE)
        if samples_by_profile:
            self._samples_by_profile.update({str(k): int(v) for k, v in samples_by_profile.items()})

        self._standard_normal = NormalDist()

    def calculate(
        self,
        legs: List[Dict[str, Any]],
        *,
        risk_profile: str = "balanced",
        rng_seed: Optional[int] = None,
    ) -> float:
        legs = list(legs or [])
        if not legs:
            return 0.0

        # Group by game_id, but avoid accidental grouping when game_id is missing.
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for idx, leg in enumerate(legs):
            raw_game_id = str(leg.get("game_id") or "").strip()
            game_id = raw_game_id if raw_game_id else f"_missing_game_id_{idx}"
            groups.setdefault(game_id, []).append(leg)

        profile = (risk_profile or "balanced").lower().strip()

        total_prob = 1.0
        for game_id, group in groups.items():
            # Ensure order-invariant determinism (callers may pass legs in any order).
            group = sorted(group, key=self._leg_sort_key)
            if len(group) == 1:
                total_prob *= self._clamp01(self._extract_probability(group[0]))
                continue

            # Same-game group: Monte Carlo joint probability for "all hit"
            num_samples = self._samples_for_group(profile, len(group))
            seed = rng_seed if rng_seed is not None else self._derive_seed(profile, game_id, group)
            group_prob = self._estimate_same_game_joint_prob(
                group,
                num_samples=num_samples,
                seed=seed,
            )
            total_prob *= group_prob

        return float(max(0.0, min(1.0, total_prob)))

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _estimate_same_game_joint_prob(self, legs: List[Dict[str, Any]], *, num_samples: int, seed: int) -> float:
        probs = [self._clamp01(self._extract_probability(leg)) for leg in legs]
        if any(p <= 0.0 for p in probs):
            return 0.0
        independent = float(np.prod(np.array(probs, dtype=float)))

        thresholds = np.array([self._inv_standard_normal(p) for p in probs], dtype=float)

        corr = self._correlation_model.build_correlation_matrix(legs)
        if not corr:
            return float(np.prod(np.array(probs, dtype=float)))

        R = np.array(corr, dtype=float)
        R = self._sanitize_corr_matrix(R)

        L = self._safe_cholesky(R)
        if L is None:
            # Fallback: avoid hard-failing; assume independence if correlation matrix is invalid.
            return independent

        rng = np.random.default_rng(int(seed) & 0xFFFFFFFF)
        z = rng.standard_normal(size=(int(num_samples), int(len(probs)))) @ L.T
        hits = (z <= thresholds).all(axis=1)
        hit_rate = float(hits.mean())
        # Rare-event safeguard: for long same-game parlays, Monte Carlo can return 0.0
        # simply because no samples hit. In that case we return the independence estimate
        # as a conservative, non-zero fallback.
        if hit_rate <= 0.0:
            return independent
        return hit_rate

    def _sanitize_corr_matrix(self, R: np.ndarray) -> np.ndarray:
        n = int(R.shape[0])
        # Force symmetry, clamp off-diagonals, and reset diagonal to 1.
        R = (R + R.T) / 2.0
        np.fill_diagonal(R, 1.0)
        R = np.clip(R, -0.99, 0.99)
        np.fill_diagonal(R, 1.0)
        if n <= 1:
            return R
        return R

    @staticmethod
    def _safe_cholesky(R: np.ndarray) -> Optional[np.ndarray]:
        n = int(R.shape[0])
        if n <= 1:
            return np.eye(n, dtype=float)

        jitter = 1e-8
        for _ in range(6):
            try:
                return np.linalg.cholesky(R)
            except np.linalg.LinAlgError:
                R = R + np.eye(n, dtype=float) * jitter
                jitter *= 10.0
        return None

    def _inv_standard_normal(self, p: float) -> float:
        # Clamp to avoid +/-inf from inv_cdf.
        p = self._clamp01(p)
        p = max(1e-6, min(1.0 - 1e-6, p))
        return float(self._standard_normal.inv_cdf(p))

    @staticmethod
    def _extract_probability(leg: Dict[str, Any]) -> float:
        # Prefer "adjusted_prob" (engine output), then "probability".
        for key in ("adjusted_prob", "probability", "prob"):
            if key in leg:
                try:
                    return float(leg.get(key) or 0.0)
                except Exception:
                    continue
        return 0.0

    @staticmethod
    def _clamp01(value: float) -> float:
        try:
            x = float(value)
        except Exception:
            return 0.0
        return max(0.0, min(1.0, x))

    @staticmethod
    def _derive_seed(profile: str, game_id: str, legs: List[Dict[str, Any]]) -> int:
        # Stable seed for deterministic outputs across processes.
        parts = []
        for leg in legs or []:
            parts.append(
                "|".join(
                    [
                        str(leg.get("market_id") or ""),
                        str(leg.get("market_type") or ""),
                        str(leg.get("outcome") or ""),
                        str(leg.get("game_id") or ""),
                    ]
                )
            )
        parts.sort()
        payload = f"{profile}::{game_id}::" + "||".join(parts)
        digest = hashlib.sha256(payload.encode("utf-8")).digest()
        # 32-bit seed for numpy default_rng compatibility.
        return int.from_bytes(digest[:4], byteorder="big", signed=False)

    @staticmethod
    def _leg_sort_key(leg: Dict[str, Any]) -> tuple:
        return (
            str(leg.get("game_id") or ""),
            str(leg.get("market_id") or ""),
            str(leg.get("market_type") or ""),
            str(leg.get("outcome") or ""),
        )

    def _samples_for_group(self, profile: str, group_size: int) -> int:
        base = int(self._samples_by_profile.get(profile, self._samples_by_profile["balanced"]))
        n = int(group_size)
        if n <= 1:
            return 0
        # 2-leg groups are very common in the main generator (max 2 legs/game),
        # so we can use fewer samples here for speed.
        if n == 2:
            samples = max(2000, base // 2)
        elif n <= 4:
            samples = base
        elif n <= 8:
            samples = int(base * 1.5)
        else:
            samples = int(base * 2.0)
        return max(500, min(50000, int(samples)))


