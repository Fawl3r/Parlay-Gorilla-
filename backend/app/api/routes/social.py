"""Social features routes - sharing, leaderboards, etc."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, Integer
from sqlalchemy.orm import joinedload
from typing import List, Optional
from pydantic import BaseModel
import uuid

from app.core.dependencies import get_db, get_current_user, get_optional_user
from app.models.user import User
from app.models.parlay import Parlay
from app.models.shared_parlay import SharedParlay, ParlayLike
from app.services.notification_service import NotificationService

router = APIRouter()


class ShareParlayRequest(BaseModel):
    """Request to share a parlay"""
    parlay_id: str
    comment: Optional[str] = None
    is_public: str = "public"  # public, unlisted, private


class ShareParlayResponse(BaseModel):
    """Response for shared parlay"""
    share_token: str
    share_url: str
    shared_at: str


@router.post("/share", response_model=ShareParlayResponse)
async def share_parlay(
    request: ShareParlayRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Share a parlay with a unique link"""
    # Verify parlay exists and belongs to user
    result = await db.execute(
        select(Parlay).where(Parlay.id == request.parlay_id)
    )
    parlay = result.scalar_one_or_none()
    
    if not parlay:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parlay not found"
        )
    
    if parlay.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only share your own parlays"
        )
    
    # Check if already shared
    result = await db.execute(
        select(SharedParlay).where(
            SharedParlay.parlay_id == request.parlay_id,
            SharedParlay.user_id == current_user.id
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        # Return existing share
        return ShareParlayResponse(
            share_token=existing.share_token,
            share_url=f"/share/{existing.share_token}",
            shared_at=existing.created_at.isoformat() if existing.created_at else ""
        )
    
    # Create new share
    notification_service = NotificationService(db)
    share_token = notification_service.generate_share_token()
    
    shared = SharedParlay(
        parlay_id=request.parlay_id,
        user_id=current_user.id,
        share_token=share_token,
        is_public=request.is_public,
        comment=request.comment
    )
    db.add(shared)
    await db.commit()
    await db.refresh(shared)
    
    return ShareParlayResponse(
        share_token=share_token,
        share_url=f"/share/{share_token}",
        shared_at=shared.created_at.isoformat() if shared.created_at else ""
    )


@router.get("/share/{share_token}")
async def get_shared_parlay(
    share_token: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Get a shared parlay by token"""
    result = await db.execute(
        select(SharedParlay)
        .options(joinedload(SharedParlay.user))
        .where(SharedParlay.share_token == share_token)
    )
    shared = result.scalar_one_or_none()
    
    if not shared:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shared parlay not found"
        )
    
    # Check privacy
    if shared.is_public == "private" and (not current_user or shared.user_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This parlay is private"
        )
    
    # Increment view count
    shared.views_count += 1
    await db.commit()
    
    # Get parlay data
    result = await db.execute(
        select(Parlay).where(Parlay.id == shared.parlay_id)
    )
    parlay = result.scalar_one_or_none()
    
    if not parlay:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parlay not found"
        )
    
    # Check if current user liked it
    is_liked = False
    if current_user:
        result = await db.execute(
            select(ParlayLike).where(
                ParlayLike.shared_parlay_id == shared.id,
                ParlayLike.user_id == current_user.id
            )
        )
        is_liked = result.scalar_one_or_none() is not None
    
    display_name = "Anonymous"
    if shared.user:
        display_name = shared.user.display_name or shared.user.username or "Anonymous"

    return {
        "parlay": {
            "id": str(parlay.id),
            "num_legs": parlay.num_legs,
            "risk_profile": parlay.risk_profile,
            "parlay_hit_prob": float(parlay.parlay_hit_prob),
            "legs": parlay.legs,
            "ai_summary": parlay.ai_summary,
            "ai_risk_notes": parlay.ai_risk_notes,
            "created_at": parlay.created_at.isoformat() if parlay.created_at else None,
        },
        "shared": {
            "comment": shared.comment,
            "views_count": shared.views_count,
            "likes_count": shared.likes_count,
            "is_liked": is_liked,
            "shared_at": shared.created_at.isoformat() if shared.created_at else None,
        },
        "user": {
            "display_name": display_name,
        }
    }


@router.post("/share/{share_token}/like")
async def like_shared_parlay(
    share_token: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Like a shared parlay"""
    result = await db.execute(
        select(SharedParlay).where(SharedParlay.share_token == share_token)
    )
    shared = result.scalar_one_or_none()
    
    if not shared:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shared parlay not found"
        )
    
    # Check if already liked
    result = await db.execute(
        select(ParlayLike).where(
            ParlayLike.shared_parlay_id == shared.id,
            ParlayLike.user_id == current_user.id
        )
    )
    existing_like = result.scalar_one_or_none()
    
    if existing_like:
        # Unlike
        await db.delete(existing_like)
        shared.likes_count = max(0, shared.likes_count - 1)
    else:
        # Like
        like = ParlayLike(
            shared_parlay_id=shared.id,
            user_id=current_user.id
        )
        db.add(like)
        shared.likes_count += 1
    
    await db.commit()
    
    return {
        "liked": existing_like is None,
        "likes_count": shared.likes_count
    }


@router.get("/feed")
async def get_social_feed(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Return recent public shared parlays for the social feed."""
    result = await db.execute(
        select(SharedParlay, User, Parlay)
        .join(User, SharedParlay.user_id == User.id)
        .join(Parlay, SharedParlay.parlay_id == Parlay.id)
        .where(SharedParlay.is_public == "public")
        .order_by(desc(SharedParlay.created_at))
        .limit(limit)
    )

    shared_rows = result.all()
    feed_items = []

    for shared, user, parlay in shared_rows:
        is_liked = False
        if current_user:
            like_result = await db.execute(
                select(ParlayLike).where(
                    ParlayLike.shared_parlay_id == shared.id,
                    ParlayLike.user_id == current_user.id,
                )
            )
            is_liked = like_result.scalar_one_or_none() is not None

        feed_items.append(
            {
                "share_token": shared.share_token,
                "comment": shared.comment,
                "created_at": shared.created_at.isoformat() if shared.created_at else None,
                "views_count": shared.views_count,
                "likes_count": shared.likes_count,
                "is_liked": is_liked,
                "parlay": {
                    "id": str(parlay.id),
                    "num_legs": parlay.num_legs,
                    "risk_profile": parlay.risk_profile,
                    "parlay_hit_prob": float(parlay.parlay_hit_prob),
                    "legs": parlay.legs,
                    "ai_summary": parlay.ai_summary,
                    "ai_risk_notes": parlay.ai_risk_notes,
                },
                "user": {
                    "id": str(user.id),
                    "display_name": user.display_name or user.username or "Anonymous",
                },
            }
        )

    return {"items": feed_items}


@router.get("/leaderboard")
async def get_leaderboard(
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Get leaderboard of top-performing parlay creators"""
    # Get users with most successful parlays
    # This is simplified - in production, would calculate more sophisticated metrics
    
    result = await db.execute(
        select(
            User.id,
            User.display_name,
            User.username,
            func.count(Parlay.id).label("total_parlays"),
            func.sum(func.cast(Parlay.parlay_hit_prob > 0.5, Integer)).label("high_prob_parlays")
        )
        .join(Parlay, User.id == Parlay.user_id)
        .group_by(User.id, User.display_name, User.username)
        .order_by(desc("total_parlays"))
        .limit(limit)
    )
    
    leaderboard = []
    for row in result:
        leaderboard.append({
            "user_id": str(row.id),
            "display_name": row.display_name or row.username or "Anonymous",
            "total_parlays": row.total_parlays,
            "high_prob_parlays": row.high_prob_parlays or 0,
        })
    
    return {"leaderboard": leaderboard}

