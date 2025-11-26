"""Report generation routes"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.report_generator import ReportGeneratorService

router = APIRouter()


@router.get("/csv")
async def get_user_report_csv(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate and download CSV report of user's parlays"""
    service = ReportGeneratorService(db)
    
    try:
        csv_content = await service.generate_user_report_csv(
            user_id=str(current_user.id),
            start_date=start_date,
            end_date=end_date
        )
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=parlays_{datetime.now().strftime('%Y%m%d')}.csv"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")


@router.get("/summary")
async def get_performance_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get performance summary for current user"""
    service = ReportGeneratorService(db)
    
    summary = await service.generate_performance_summary(
        user_id=str(current_user.id)
    )
    
    return summary


@router.get("/weekly")
async def get_weekly_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get weekly performance summary"""
    service = ReportGeneratorService(db)
    
    summary = await service.generate_weekly_summary(
        user_id=str(current_user.id)
    )
    
    return summary

