"""Scheduler job for awarding arcade points to eligible verified wins."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, exists, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import AsyncSessionLocal
from app.models.arcade_points_event import ArcadePointsEvent
from app.models.arcade_points_totals import ArcadePointsTotals
from app.models.saved_parlay import SavedParlay, SavedParlayType
from app.models.saved_parlay_results import SavedParlayResult
from app.models.verification_record import VerificationRecord, VerificationStatus
from app.models.shared_parlay import SharedParlay
from app.services.leaderboards.arcade_points_calculator import ArcadePointsCalculator


class ArcadePointsAwardJob:
    """Background job to award arcade points for eligible verified wins."""

    async def run(self) -> None:
        """Run the arcade points award job."""
        async with AsyncSessionLocal() as db:
            try:
                awarded = await self._award_eligible_wins(db)
                if awarded > 0:
                    print(f"[SCHEDULER] Awarded arcade points for {awarded} verified wins")
            except Exception as e:
                print(f"[SCHEDULER] Error awarding arcade points: {e}")
                import traceback

                traceback.print_exc()

    async def _award_eligible_wins(self, db: AsyncSession) -> int:
        """
        Find and award points for newly-eligible wins.

        Eligibility criteria:
        - saved_parlay.parlay_type == 'custom'
        - saved_parlay_result.hit == True
        - saved_parlay_result.num_legs >= 5
        - verification_record exists with status='confirmed' for the saved_parlay_id
        - verification_record.data_hash matches saved_parlay.content_hash (current version)
        - No existing arcade_points_event for this saved_parlay_result_id

        Returns:
            Number of wins awarded
        """
        # Find eligible wins that haven't been awarded yet
        query = (
            select(SavedParlayResult, SavedParlay)
            .join(SavedParlay, SavedParlayResult.saved_parlay_id == SavedParlay.id)
            .where(SavedParlayResult.parlay_type == SavedParlayType.custom.value)
            .where(SavedParlayResult.hit.is_(True))
            .where(SavedParlayResult.num_legs >= 5)
            .where(
                exists(
                    select(1)
                    .select_from(VerificationRecord)
                    .where(VerificationRecord.saved_parlay_id == SavedParlayResult.saved_parlay_id)
                    .where(VerificationRecord.user_id == SavedParlayResult.user_id)
                    .where(VerificationRecord.status == VerificationStatus.confirmed.value)
                    .where(VerificationRecord.data_hash == SavedParlay.content_hash)
                )
            )
            .where(
                ~exists(
                    select(1)
                    .select_from(ArcadePointsEvent)
                    .where(ArcadePointsEvent.saved_parlay_result_id == SavedParlayResult.id)
                )
            )
            .order_by(SavedParlayResult.resolved_at.desc())
            .limit(100)
        )

        result = await db.execute(query)
        rows = result.all()

        awarded_count = 0
        for saved_result, saved_parlay in rows:
            try:
                if await self._award_points_for_win(db, saved_result=saved_result, saved_parlay=saved_parlay):
                    awarded_count += 1
            except Exception as e:
                print(f"[ARCADE_POINTS] Error awarding points for result {saved_result.id}: {e}")
                continue

        return awarded_count

    async def _award_points_for_win(
        self, db: AsyncSession, *, saved_result: SavedParlayResult, saved_parlay: SavedParlay
    ) -> bool:
        """Award points for a single eligible win and update totals."""
        num_legs = saved_result.num_legs
        if not ArcadePointsCalculator.is_eligible(num_legs):
            return False

        points = ArcadePointsCalculator.calculate_points(num_legs)

        # Create event
        event = ArcadePointsEvent(
            user_id=saved_result.user_id,
            saved_parlay_id=saved_result.saved_parlay_id,
            saved_parlay_result_id=saved_result.id,
            num_legs=num_legs,
            points_awarded=points,
        )
        db.add(event)

        # Update or create totals
        totals_result = await db.execute(
            select(ArcadePointsTotals).where(ArcadePointsTotals.user_id == saved_result.user_id).limit(1)
        )
        totals = totals_result.scalar_one_or_none()

        if totals is None:
            totals = ArcadePointsTotals(
                user_id=saved_result.user_id,
                total_points=points,
                total_qualifying_wins=1,
                last_win_at=saved_result.resolved_at,
            )
            db.add(totals)
        else:
            totals.total_points += points
            totals.total_qualifying_wins += 1
            if saved_result.resolved_at and (
                totals.last_win_at is None or saved_result.resolved_at > totals.last_win_at
            ):
                totals.last_win_at = saved_result.resolved_at

        # Auto-post to community feed if user is public/anonymous
        await self._auto_post_win_to_feed(db, saved_result=saved_result, saved_parlay=saved_parlay)

        await db.commit()
        return True

    async def _auto_post_win_to_feed(
        self, db: AsyncSession, *, saved_result: SavedParlayResult, saved_parlay: SavedParlay
    ) -> None:
        """Auto-post winning parlay to community feed if user visibility allows."""
        from app.models.user import User

        # Check user visibility
        user_result = await db.execute(select(User).where(User.id == saved_result.user_id).limit(1))
        user = user_result.scalar_one_or_none()
        if not user:
            return

        visibility = str(getattr(user, "leaderboard_visibility", "public") or "public").strip().lower()
        if visibility == "hidden":
            return

        # Check if already shared
        existing_result = await db.execute(
            select(SharedParlay).where(
                and_(
                    SharedParlay.parlay_id.is_(None),  # SharedParlay uses parlay_id, but we have saved_parlay
                    SharedParlay.user_id == saved_result.user_id,
                )
            )
            .where(SharedParlay.share_token.like(f"%{str(saved_parlay.id)}%"))
            .limit(1)
        )
        if existing_result.scalar_one_or_none():
            return

        # Note: SharedParlay currently links to `parlays` table, not `saved_parlays`.
        # For now, we'll skip auto-posting saved parlays to the feed until we extend
        # the shared_parlay model to support saved_parlay_id.
        # This is a known limitation - we can extend it later if needed.
        # For MVP, the win feed endpoint will show wins directly from arcade_points_events.

