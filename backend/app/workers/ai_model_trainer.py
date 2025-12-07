"""AI model trainer worker for improving parlay predictions"""

import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database.session import AsyncSessionLocal
from app.models.parlay_results import ParlayResult
from app.models.game_results import GameResult


class AIModelTrainer:
    """Background worker for training and improving AI models"""
    
    async def analyze_performance(self):
        """Analyze parlay prediction performance and adjust weights"""
        async with AsyncSessionLocal() as db:
            try:
                # Get recent parlay results
                cutoff_date = datetime.utcnow() - timedelta(days=30)
                
                result = await db.execute(
                    select(ParlayResult)
                    .where(ParlayResult.created_at >= cutoff_date)
                    .where(ParlayResult.hit.isnot(None))  # Only resolved parlays
                )
                resolved_parlays = result.scalars().all()
                
                if not resolved_parlays:
                    print("[AI_TRAINER] No resolved parlays to analyze")
                    return
                
                # Calculate accuracy metrics
                total = len(resolved_parlays)
                hits = sum(1 for p in resolved_parlays if p.hit)
                misses = total - hits
                
                # Calculate calibration error
                total_predicted_prob = sum(float(p.predicted_probability) for p in resolved_parlays)
                actual_rate = hits / total if total > 0 else 0
                predicted_rate = total_predicted_prob / total if total > 0 else 0
                calibration_error = abs(actual_rate - predicted_rate)
                
                print(f"[AI_TRAINER] Performance Analysis:")
                print(f"  Total Parlays: {total}")
                print(f"  Hits: {hits} ({hits/total*100:.1f}%)")
                print(f"  Misses: {misses} ({misses/total*100:.1f}%)")
                print(f"  Calibration Error: {calibration_error:.3f}")
                print(f"  Predicted Rate: {predicted_rate:.1%}")
                print(f"  Actual Rate: {actual_rate:.1%}")
                
                # Analyze by risk profile
                for risk_profile in ["conservative", "balanced", "degen"]:
                    profile_parlays = [p for p in resolved_parlays if p.risk_profile == risk_profile]
                    if profile_parlays:
                        profile_hits = sum(1 for p in profile_parlays if p.hit)
                        profile_rate = profile_hits / len(profile_parlays)
                        print(f"  {risk_profile.capitalize()}: {profile_hits}/{len(profile_parlays)} ({profile_rate:.1%})")
                
                # Store metrics (could create a ModelMetrics table)
                # For now, just log
                
            except Exception as e:
                print(f"[AI_TRAINER] Error analyzing performance: {e}")
    
    async def update_model_weights(self):
        """Update model weights based on recent performance"""
        # This would implement actual ML weight updates
        # For now, it's a placeholder
        print("[AI_TRAINER] Model weight update (placeholder)")
        await self.analyze_performance()
    
    async def train_on_game_results(self):
        """Train model on historical game results"""
        async with AsyncSessionLocal() as db:
            try:
                # Get recent game results
                cutoff_date = datetime.utcnow() - timedelta(days=90)
                
                result = await db.execute(
                    select(func.count()).select_from(GameResult)
                    .where(GameResult.game_date >= cutoff_date)
                    .where(GameResult.completed == "true")
                )
                game_count = result.scalar()
                
                print(f"[AI_TRAINER] Found {game_count} recent game results for training")
                
                # In a real implementation, this would:
                # 1. Extract features from game results
                # 2. Train ML models
                # 3. Update model weights
                # 4. Save updated models
                
            except Exception as e:
                print(f"[AI_TRAINER] Error training on game results: {e}")


async def run_ai_trainer():
    """Main entry point for AI trainer worker"""
    trainer = AIModelTrainer()
    await trainer.analyze_performance()
    await trainer.train_on_game_results()


if __name__ == "__main__":
    asyncio.run(run_ai_trainer())

