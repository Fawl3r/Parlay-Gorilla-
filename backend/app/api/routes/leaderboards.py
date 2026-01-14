"""Leaderboards API routes.

Two leaderboards (per product spec):
- Verified Winners: custom saved parlays that were explicitly verified and WON
- AI Power Users: engagement leaderboard based on AI parlay generation volume

These endpoints are designed to be cacheable and never leak private user data.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel
from sqlalchemy import case, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.models.parlay import Parlay
from app.models.saved_parlay import SavedParlay, SavedParlayType
from app.models.saved_parlay_results import SavedParlayResult
from app.models.user import User
from app.models.verification_record import VerificationRecord, VerificationStatus
from app.models.arcade_points_totals import ArcadePointsTotals
from app.models.arcade_points_event import ArcadePointsEvent

router = APIRouter()


class VerifiedWinnersEntry(BaseModel):
    rank: int
    username: str
    verified_wins: int
    win_rate: float
    last_win_at: Optional[str] = None
    inscription_id: Optional[str] = None


class VerifiedWinnersResponse(BaseModel):
    leaderboard: List[VerifiedWinnersEntry]


class AiPowerUsersEntry(BaseModel):
    rank: int
    username: str
    ai_parlays_generated: int
    last_generated_at: Optional[str] = None


class AiPowerUsersResponse(BaseModel):
    timeframe: str
    leaderboard: List[AiPowerUsersEntry]


def _safe_display_name(
    *,
    display_name: Optional[str],
    username: Optional[str],
    account_number: Optional[str],
    leaderboard_visibility: Optional[str],
) -> Optional[str]:
    vis = (leaderboard_visibility or "public").strip().lower()
    if vis == "hidden":
        return None

    acct = (account_number or "").strip()
    suffix = acct[-4:] if len(acct) >= 4 else "0000"

    if vis == "anonymous":
        return f"Gorilla_{suffix}"

    name = (display_name or "").strip()
    if name:
        return name
    uname = (username or "").strip()
    if uname:
        return uname
    return f"Gorilla_{suffix}"


async def _find_last_win_inscription_id(
    db: AsyncSession, *, user_id, last_win_at: Optional[datetime]
) -> Optional[str]:
    if not last_win_at:
        return None
    res = await db.execute(
        select(VerificationRecord.tx_digest, VerificationRecord.object_id, VerificationRecord.data_hash)
        .select_from(VerificationRecord)
        .join(
            SavedParlayResult,
            (SavedParlayResult.saved_parlay_id == VerificationRecord.saved_parlay_id)
            & (SavedParlayResult.user_id == VerificationRecord.user_id),
        )
        .where(VerificationRecord.user_id == user_id)
        .where(VerificationRecord.status == VerificationStatus.confirmed.value)
        .where(SavedParlayResult.parlay_type == SavedParlayType.custom.value)
        .where(SavedParlayResult.hit.is_(True))
        .where(SavedParlayResult.resolved_at == last_win_at)
        .order_by(VerificationRecord.created_at.desc())
        .limit(1)
    )
    row = res.first()
    if not row:
        return None
    tx, object_id, data_hash = row
    tx_str = str(tx or "").strip()
    if tx_str:
        return tx_str
    obj_str = str(object_id or "").strip()
    if obj_str:
        return obj_str
    hash_str = str(data_hash or "").strip()
    return hash_str or None


@router.get("/leaderboards/custom", response_model=VerifiedWinnersResponse)
async def get_custom_verified_winners(
    response: Response,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Verified Winners leaderboard.

    Includes users with at least one winning, resolved, confirmed verification record for a custom saved parlay.
    """
    response.headers["Cache-Control"] = "public, max-age=60"

    wins_expr = func.sum(case((SavedParlayResult.hit.is_(True), 1), else_=0))
    total_expr = func.count(SavedParlayResult.id)
    win_rate_expr = (wins_expr * 1.0) / func.nullif(total_expr, 0)
    last_win_expr = func.max(case((SavedParlayResult.hit.is_(True), SavedParlayResult.resolved_at), else_=None))

    q = (
        select(
            User.id.label("user_id"),
            User.display_name.label("display_name"),
            User.username.label("username"),
            User.account_number.label("account_number"),
            User.leaderboard_visibility.label("leaderboard_visibility"),
            wins_expr.label("verified_wins"),
            win_rate_expr.label("win_rate"),
            last_win_expr.label("last_win_at"),
        )
        .select_from(SavedParlayResult)
        .join(User, User.id == SavedParlayResult.user_id)
        .where(SavedParlayResult.parlay_type == SavedParlayType.custom.value)
        .where(
            exists(
                select(1)
                .select_from(VerificationRecord)
                .where(VerificationRecord.user_id == SavedParlayResult.user_id)
                .where(VerificationRecord.saved_parlay_id == SavedParlayResult.saved_parlay_id)
                .where(VerificationRecord.status == VerificationStatus.confirmed.value)
            )
        )
        .where(SavedParlayResult.hit.isnot(None))
        .where(User.leaderboard_visibility != "hidden")
        .group_by(User.id, User.display_name, User.username, User.account_number)
        .having(wins_expr > 0)
        .order_by(wins_expr.desc(), win_rate_expr.desc(), last_win_expr.desc())
        .limit(int(limit))
    )

    res = await db.execute(q)
    rows = res.all()

    leaderboard: List[VerifiedWinnersEntry] = []
    for row in rows:
        user_id, display_name, username, account_number, leaderboard_visibility, wins, win_rate, last_win_at = row
        name = _safe_display_name(
            display_name=display_name,
            username=username,
            account_number=account_number,
            leaderboard_visibility=leaderboard_visibility,
        )
        if not name:
            continue
        inscription_id = await _find_last_win_inscription_id(db, user_id=user_id, last_win_at=last_win_at)
        leaderboard.append(
            VerifiedWinnersEntry(
                rank=len(leaderboard) + 1,
                username=name,
                verified_wins=int(wins or 0),
                win_rate=float(win_rate or 0.0),
                last_win_at=last_win_at.astimezone(timezone.utc).isoformat() if last_win_at else None,
                inscription_id=inscription_id,
            )
        )

    return VerifiedWinnersResponse(leaderboard=leaderboard)


def _cutoff_for_period(period: str) -> Tuple[str, Optional[datetime]]:
    p = (period or "").strip().lower()
    if p in {"all", "all_time", "all-time"}:
        return "all_time", None
    # Default: rolling 30d
    now = datetime.now(timezone.utc)
    return "30d", now - timedelta(days=30)


@router.get("/leaderboards/ai-usage", response_model=AiPowerUsersResponse)
async def get_ai_power_users(
    response: Response,
    period: str = Query("30d", pattern="^(30d|all_time)$"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    AI Power Users leaderboard (engagement).

    Baseline implementation: counts AI generations from `parlays` plus saved custom parlays
    (`saved_parlays` where parlay_type=custom).
    """
    response.headers["Cache-Control"] = "public, max-age=60"

    timeframe, cutoff = _cutoff_for_period(period)

    # 1) AI parlay generations (`parlays`)
    q_ai = (
        select(
            Parlay.user_id.label("user_id"),
            func.count(Parlay.id).label("count"),
            func.max(Parlay.created_at).label("last_at"),
        )
        .where(Parlay.user_id.isnot(None))
        .group_by(Parlay.user_id)
    )
    if cutoff is not None:
        q_ai = q_ai.where(Parlay.created_at >= cutoff)

    # 2) Custom saved parlays (`saved_parlays` where custom)
    q_custom = (
        select(
            SavedParlay.user_id.label("user_id"),
            func.count(SavedParlay.id).label("count"),
            func.max(SavedParlay.created_at).label("last_at"),
        )
        .where(SavedParlay.user_id.isnot(None))
        .where(SavedParlay.parlay_type == SavedParlayType.custom.value)
        .group_by(SavedParlay.user_id)
    )
    if cutoff is not None:
        q_custom = q_custom.where(SavedParlay.created_at >= cutoff)

    res_ai = await db.execute(q_ai)
    res_custom = await db.execute(q_custom)

    by_user: Dict[str, Dict[str, object]] = {}

    for user_id, count, last_at in res_ai.all():
        by_user[str(user_id)] = {
            "user_id": user_id,
            "count": int(count or 0),
            "last_at": last_at,
        }

    for user_id, count, last_at in res_custom.all():
        key = str(user_id)
        existing = by_user.get(key)
        if existing is None:
            by_user[key] = {"user_id": user_id, "count": int(count or 0), "last_at": last_at}
            continue
        existing["count"] = int(existing.get("count", 0) or 0) + int(count or 0)
        prev_last = existing.get("last_at")
        if prev_last is None or (last_at and last_at > prev_last):
            existing["last_at"] = last_at

    user_ids = [v["user_id"] for v in by_user.values() if v.get("user_id") is not None]
    if not user_ids:
        return AiPowerUsersResponse(timeframe=timeframe, leaderboard=[])

    users_res = await db.execute(
        select(User.id, User.display_name, User.username, User.account_number, User.leaderboard_visibility).where(
            User.id.in_(user_ids)
        )
    )
    users = {str(row[0]): row for row in users_res.all()}

    items: List[Tuple[int, Optional[datetime], str]] = []
    for k, v in by_user.items():
        user_row = users.get(k)
        if not user_row:
            continue
        _, display_name, username, account_number, leaderboard_visibility = user_row
        if str(leaderboard_visibility or "public").strip().lower() == "hidden":
            continue
        count = int(v.get("count", 0) or 0)
        if count <= 0:
            continue
        last_at = v.get("last_at")
        name = _safe_display_name(
            display_name=display_name,
            username=username,
            account_number=account_number,
            leaderboard_visibility=leaderboard_visibility,
        )
        if not name:
            continue
        items.append((count, last_at if isinstance(last_at, datetime) else None, name))

    items.sort(key=lambda x: (x[0], x[1] or datetime.fromtimestamp(0, tz=timezone.utc)), reverse=True)

    leaderboard: List[AiPowerUsersEntry] = []
    for idx, (count, last_at, name) in enumerate(items[: int(limit)], start=1):
        leaderboard.append(
            AiPowerUsersEntry(
                rank=idx,
                username=name,
                ai_parlays_generated=int(count),
                last_generated_at=last_at.astimezone(timezone.utc).isoformat() if last_at else None,
            )
        )

    return AiPowerUsersResponse(timeframe=timeframe, leaderboard=leaderboard)


class ArcadePointsEntry(BaseModel):
    rank: int
    username: str
    total_points: int
    total_qualifying_wins: int
    last_win_at: Optional[str] = None


class ArcadePointsResponse(BaseModel):
    period: str
    leaderboard: List[ArcadePointsEntry]


class RecentWinFeedItem(BaseModel):
    username: str
    points_awarded: int
    num_legs: int
    parlay_title: Optional[str] = None
    resolved_at: str


class RecentWinsFeedResponse(BaseModel):
    wins: List[RecentWinFeedItem]


@router.get("/leaderboards/arcade-points", response_model=ArcadePointsResponse)
async def get_arcade_points_leaderboard(
    response: Response,
    period: str = Query("all_time", pattern="^(30d|all_time)$"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Arcade Points leaderboard.

    Shows users ranked by total arcade points from verified 5+ leg wins.
    Only includes users with public or anonymous visibility.
    """
    response.headers["Cache-Control"] = "public, max-age=60"

    timeframe, cutoff = _cutoff_for_period(period)

    query = (
        select(
            ArcadePointsTotals.user_id,
            ArcadePointsTotals.total_points,
            ArcadePointsTotals.total_qualifying_wins,
            ArcadePointsTotals.last_win_at,
            User.display_name,
            User.username,
            User.account_number,
            User.leaderboard_visibility,
        )
        .select_from(ArcadePointsTotals)
        .join(User, User.id == ArcadePointsTotals.user_id)
        .where(User.leaderboard_visibility != "hidden")
        .where(ArcadePointsTotals.total_points > 0)
    )

    if cutoff is not None:
        # For 30d period, filter by last_win_at
        query = query.where(
            (ArcadePointsTotals.last_win_at.isnot(None)) & (ArcadePointsTotals.last_win_at >= cutoff)
        )

    query = query.order_by(ArcadePointsTotals.total_points.desc(), ArcadePointsTotals.last_win_at.desc()).limit(
        int(limit)
    )

    result = await db.execute(query)
    rows = result.all()

    leaderboard: List[ArcadePointsEntry] = []
    for idx, row in enumerate(rows, start=1):
        (
            user_id,
            total_points,
            total_wins,
            last_win_at,
            display_name,
            username,
            account_number,
            leaderboard_visibility,
        ) = row

        name = _safe_display_name(
            display_name=display_name,
            username=username,
            account_number=account_number,
            leaderboard_visibility=leaderboard_visibility,
        )
        if not name:
            continue

        leaderboard.append(
            ArcadePointsEntry(
                rank=idx,
                username=name,
                total_points=int(total_points or 0),
                total_qualifying_wins=int(total_wins or 0),
                last_win_at=last_win_at.astimezone(timezone.utc).isoformat() if last_win_at else None,
            )
        )

    return ArcadePointsResponse(period=timeframe, leaderboard=leaderboard)


@router.get("/leaderboards/arcade-wins", response_model=RecentWinsFeedResponse)
async def get_recent_arcade_wins_feed(
    response: Response,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Recent Verified Wins feed.

    Shows recent arcade points awards (verified 5+ leg wins) from users with
    public or anonymous visibility. Ordered by most recent first.
    """
    response.headers["Cache-Control"] = "public, max-age=60"

    query = (
        select(
            ArcadePointsEvent.points_awarded,
            ArcadePointsEvent.num_legs,
            ArcadePointsEvent.created_at,
            SavedParlay.title,
            User.display_name,
            User.username,
            User.account_number,
            User.leaderboard_visibility,
        )
        .select_from(ArcadePointsEvent)
        .join(User, User.id == ArcadePointsEvent.user_id)
        .join(SavedParlay, SavedParlay.id == ArcadePointsEvent.saved_parlay_id)
        .where(User.leaderboard_visibility != "hidden")
        .order_by(ArcadePointsEvent.created_at.desc())
        .limit(int(limit))
    )

    result = await db.execute(query)
    rows = result.all()

    wins: List[RecentWinFeedItem] = []
    for row in rows:
        (
            points_awarded,
            num_legs,
            created_at,
            parlay_title,
            display_name,
            username,
            account_number,
            leaderboard_visibility,
        ) = row

        name = _safe_display_name(
            display_name=display_name,
            username=username,
            account_number=account_number,
            leaderboard_visibility=leaderboard_visibility,
        )
        if not name:
            continue

        wins.append(
            RecentWinFeedItem(
                username=name,
                points_awarded=int(points_awarded or 0),
                num_legs=int(num_legs or 0),
                parlay_title=str(parlay_title).strip() if parlay_title else None,
                resolved_at=created_at.astimezone(timezone.utc).isoformat() if created_at else "",
            )
        )

    return RecentWinsFeedResponse(wins=wins)


