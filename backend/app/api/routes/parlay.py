"""Parlay API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, List

from app.core.dependencies import get_db, get_optional_user
from app.models.user import User
from app.schemas.parlay import (
    ParlayRequest,
    ParlayResponse,
    TripleParlayRequest,
    TripleParlayResponse,
)
from app.services.parlay_builder import ParlayBuilderService
from app.services.openai_service import OpenAIService
from app.services.cache_manager import CacheManager
from app.models.parlay import Parlay
from app.middleware.rate_limiter import rate_limit
import uuid

router = APIRouter()


def _get_confidence_color(score: float) -> str:
    """Get color based on confidence score"""
    if score >= 70:
        return "green"
    elif score >= 50:
        return "yellow"
    else:
        return "red"


async def _prepare_parlay_response(
    parlay_data: Dict,
    risk_profile: str,
    openai_service: OpenAIService,
    db: AsyncSession,
    current_user: Optional[User],
    explanation_override: Optional[Dict[str, str]] = None,
) -> ParlayResponse:
    """Generate AI explanation, persist parlay, and return ParlayResponse."""
    if explanation_override:
        explanation = explanation_override
    else:
        explanation = await openai_service.generate_parlay_explanation(
            legs=parlay_data["legs"],
            risk_profile=risk_profile,
            parlay_probability=parlay_data["parlay_hit_prob"],
            overall_confidence=parlay_data["overall_confidence"],
        )

    confidence_meter = {
        "score": parlay_data["overall_confidence"],
        "color": _get_confidence_color(parlay_data["overall_confidence"]),
    }

    parlay_id = str(uuid.uuid4())
    try:
        parlay = Parlay(
            legs=parlay_data["legs"],
            num_legs=parlay_data["num_legs"],
            parlay_hit_prob=parlay_data["parlay_hit_prob"],
            risk_profile=risk_profile,
            ai_summary=explanation["summary"],
            ai_risk_notes=explanation["risk_notes"],
            user_id=current_user.id if current_user and hasattr(current_user, "id") else None,
        )
        db.add(parlay)
        await db.flush()
        parlay_id = str(parlay.id)
    except Exception as db_error:
        print(f"Warning: Failed to save parlay to database: {db_error}")
        import traceback

        traceback.print_exc()

    response = ParlayResponse(
        id=parlay_id,
        legs=parlay_data["legs"],
        num_legs=int(parlay_data["num_legs"]),
        parlay_hit_prob=float(parlay_data["parlay_hit_prob"]),
        risk_profile=str(risk_profile),
        confidence_scores=[float(c) for c in parlay_data["confidence_scores"]],
        overall_confidence=float(parlay_data["overall_confidence"]),
        ai_summary=str(explanation["summary"]),
        ai_risk_notes=str(explanation["risk_notes"]),
        confidence_meter=confidence_meter,
    )

    return response


@router.post("/parlay/suggest", response_model=ParlayResponse)
@rate_limit("20/hour")  # Limit expensive parlay generation
async def suggest_parlay(
    request: Request,
    parlay_request: ParlayRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Generate a parlay suggestion based on parameters"""
    try:
        import traceback
        print(f"Parlay request received: num_legs={parlay_request.num_legs}, risk_profile={parlay_request.risk_profile}")
        
        # Check cache first
        cache_manager = CacheManager(db)
        cached_parlay = await cache_manager.get_cached_parlay(
            num_legs=parlay_request.num_legs,
            risk_profile=parlay_request.risk_profile,
            sport="NFL",
            max_age_hours=6  # Cache for 6 hours
        )
        
        if cached_parlay:
            print("Using cached parlay data")
            parlay_data = cached_parlay
        else:
            # Build parlay
            builder = ParlayBuilderService(db)
            parlay_data = await builder.build_parlay(
                num_legs=parlay_request.num_legs,
                risk_profile=parlay_request.risk_profile
            )
            
            # Cache the result
            await cache_manager.set_cached_parlay(
                num_legs=parlay_request.num_legs,
                risk_profile=parlay_request.risk_profile,
                parlay_data=parlay_data,
                sport="NFL",
                ttl_hours=6
            )
        
        print(f"Parlay data built: {len(parlay_data.get('legs', []))} legs")
        
        openai_service = OpenAIService()
        try:
            response = await _prepare_parlay_response(
                parlay_data=parlay_data,
                risk_profile=parlay_request.risk_profile,
                openai_service=openai_service,
                db=db,
                current_user=current_user,
            )
        except Exception as e:
            import traceback

            print(f"Error building response: {e}")
            print(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Error building response: {str(e)}")
        
        try:
            await db.commit()
        except Exception as commit_error:
            print(f"Warning: Failed to commit parlay: {commit_error}")
            await db.rollback()
        
        return response
        
    except ValueError as e:
        import traceback
        print(f"ValueError in parlay generation: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        print(f"Exception in parlay generation: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to generate parlay: {str(e)}")


@router.post("/parlay/suggest/triple", response_model=TripleParlayResponse)
@rate_limit("10/hour")
async def suggest_triple_parlay(
    request: Request,
    triple_request: TripleParlayRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Generate Safe/Balanced/Degen parlays in a single request."""
    try:
        sports = triple_request.sports or ["NFL"]
        leg_overrides = {
            "safe": triple_request.safe_legs,
            "balanced": triple_request.balanced_legs,
            "degen": triple_request.degen_legs,
        }
        leg_overrides = {k: v for k, v in leg_overrides.items() if v is not None}

        builder = ParlayBuilderService(db, sports[0])
        triple_data = await builder.build_triple_parlay(
            sports=sports,
            leg_overrides=leg_overrides,
        )

        openai_service = OpenAIService()
        ai_explanations = await openai_service.generate_triple_parlay_explanations(triple_data)
        responses: Dict[str, ParlayResponse] = {}
        metadata: Dict[str, Dict] = {}

        for profile_name in ["safe", "balanced", "degen"]:
            block = triple_data.get(profile_name)
            if not block:
                raise HTTPException(status_code=500, detail=f"Missing data for {profile_name} parlay")
            parlay_response = await _prepare_parlay_response(
                parlay_data=block["parlay"],
                risk_profile=block["parlay"].get("risk_profile", profile_name),
                openai_service=openai_service,
                db=db,
                current_user=current_user,
                explanation_override={
                    "summary": ai_explanations.get(profile_name, {}).get("summary", ""),
                    "risk_notes": ai_explanations.get(profile_name, {}).get("risk_notes", ""),
                },
            )
            # Attach highlight leg metadata
            highlight = ai_explanations.get(profile_name, {}).get("highlight_leg")
            metadata_block = block.get("config", {}).copy()
            if highlight:
                metadata_block["highlight_leg"] = highlight
            metadata[profile_name] = metadata_block
            responses[profile_name] = parlay_response

        try:
            await db.commit()
        except Exception as commit_error:
            print(f"Warning: Failed to commit triple parlay: {commit_error}")
            await db.rollback()

        return TripleParlayResponse(
            safe=responses["safe"],
            balanced=responses["balanced"],
            degen=responses["degen"],
            metadata=metadata,
        )

    except ValueError as e:
        import traceback

        print(f"ValueError in triple parlay generation: {e}")
        print(traceback.format_exc())
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback

        print(f"Exception in triple parlay generation: {e}")
        print(traceback.format_exc())
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to generate triple parlays: {str(e)}")

