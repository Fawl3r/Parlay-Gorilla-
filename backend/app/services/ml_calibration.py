"""ML-based probability calibration using scikit-learn"""

from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import numpy as np

from app.models.parlay_results import ParlayResult


class MLCalibrationService:
    """Service for calibrating probabilities using ML models"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._calibration_model = None
    
    async def train_calibration_model(self) -> Dict:
        """
        Train a calibration model based on historical parlay results
        
        Uses simple linear regression to adjust predicted probabilities
        based on actual outcomes
        """
        # Get historical results
        result = await self.db.execute(
            select(ParlayResult)
            .where(ParlayResult.hit.isnot(None))
            .where(ParlayResult.predicted_probability.isnot(None))
        )
        results = result.scalars().all()
        
        if len(results) < 10:
            # Not enough data for training
            return {
                "trained": False,
                "message": "Not enough historical data (need at least 10 resolved parlays)",
                "sample_size": len(results)
            }
        
        # Prepare training data
        X = np.array([[r.predicted_probability] for r in results])
        y = np.array([1.0 if r.hit else 0.0 for r in results])
        
        # Simple linear calibration: adjust predicted prob based on actual hit rate
        # This is a simplified approach - in production, use sklearn's calibration
        predicted_probs = X.flatten()
        actual_hits = y
        
        # Calculate calibration curve
        bins = np.linspace(0, 1, 11)  # 10 bins
        bin_indices = np.digitize(predicted_probs, bins) - 1
        bin_indices = np.clip(bin_indices, 0, len(bins) - 2)
        
        calibration_map = {}
        for i in range(len(bins) - 1):
            mask = bin_indices == i
            if np.sum(mask) > 0:
                actual_rate = np.mean(actual_hits[mask])
                predicted_center = (bins[i] + bins[i + 1]) / 2
                calibration_map[predicted_center] = actual_rate
        
        self._calibration_map = calibration_map
        
        # Calculate calibration error
        calibration_errors = [abs(r.predicted_probability - (1.0 if r.hit else 0.0)) 
                             for r in results]
        avg_error = np.mean(calibration_errors)
        
        return {
            "trained": True,
            "sample_size": len(results),
            "avg_calibration_error": float(avg_error),
            "calibration_bins": len(calibration_map),
            "message": f"Model trained on {len(results)} samples"
        }
    
    def calibrate_probability(self, predicted_prob: float) -> float:
        """
        Calibrate a predicted probability using the trained model
        
        Args:
            predicted_prob: Original predicted probability (0-1)
        
        Returns:
            Calibrated probability (0-1)
        """
        if not hasattr(self, '_calibration_map') or not self._calibration_map:
            # No calibration model, return original
            return predicted_prob
        
        # Find closest bin
        calibration_keys = sorted(self._calibration_map.keys())
        if not calibration_keys:
            return predicted_prob
        
        # Find nearest calibration point
        closest_key = min(calibration_keys, key=lambda x: abs(x - predicted_prob))
        calibrated = self._calibration_map[closest_key]
        
        # Blend original and calibrated (weighted average)
        # Use 70% calibrated, 30% original for stability
        return 0.7 * calibrated + 0.3 * predicted_prob
    
    async def get_calibration_stats(self) -> Dict:
        """Get calibration statistics"""
        result = await self.db.execute(
            select(ParlayResult)
            .where(ParlayResult.hit.isnot(None))
        )
        results = result.scalars().all()
        
        if not results:
            return {
                "total_samples": 0,
                "calibration_available": False
            }
        
        # Calculate Brier score (lower is better)
        brier_scores = [
            (r.predicted_probability - (1.0 if r.hit else 0.0)) ** 2
            for r in results
        ]
        avg_brier = np.mean(brier_scores) if brier_scores else 0.0
        
        # Calculate calibration by probability ranges
        ranges = {
            "0.0-0.2": [],
            "0.2-0.4": [],
            "0.4-0.6": [],
            "0.6-0.8": [],
            "0.8-1.0": []
        }
        
        for r in results:
            prob = r.predicted_probability
            if prob < 0.2:
                ranges["0.0-0.2"].append(1.0 if r.hit else 0.0)
            elif prob < 0.4:
                ranges["0.2-0.4"].append(1.0 if r.hit else 0.0)
            elif prob < 0.6:
                ranges["0.4-0.6"].append(1.0 if r.hit else 0.0)
            elif prob < 0.8:
                ranges["0.6-0.8"].append(1.0 if r.hit else 0.0)
            else:
                ranges["0.8-1.0"].append(1.0 if r.hit else 0.0)
        
        calibration_by_range = {
            range_name: {
                "predicted_avg": float(np.mean([r.predicted_probability for r in results 
                                               if self._in_range(r.predicted_probability, range_name)])),
                "actual_rate": float(np.mean(hits)) if (hits := ranges[range_name]) else 0.0,
                "sample_size": len(ranges[range_name])
            }
            for range_name in ranges.keys()
        }
        
        return {
            "total_samples": len(results),
            "avg_brier_score": float(avg_brier),
            "calibration_by_range": calibration_by_range,
            "calibration_available": True
        }
    
    def _in_range(self, value: float, range_str: str) -> bool:
        """Check if value is in range string like '0.2-0.4'"""
        parts = range_str.split("-")
        if len(parts) != 2:
            return False
        low, high = float(parts[0]), float(parts[1])
        return low <= value < high

