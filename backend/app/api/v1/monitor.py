"""
Monitor API Routes — Real-time position tracking and manual watcher triggers.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.database import get_db
from app.api.deps import get_current_user, get_master_user
from app.models.user import User
from app.services.position_monitor import PositionMonitor

router = APIRouter()
monitor_service = PositionMonitor()

@router.post("/check", response_model=Dict[str, Any])
async def check_user_positions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger a position check for the current user.
    """
    try:
        # Currently PositionMonitor.check_all_positions scans everyone.
        # We can optimize it later to take a user_id filter if needed.
        # For now, it returns a summary.
        summary = await monitor_service.check_all_positions(db)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Position check failed: {str(e)}"
        )

@router.post("/check-all", response_model=Dict[str, Any])
async def check_all_positions(
    master_user: User = Depends(get_master_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger a global position check for ALL users (Master only).
    """
    try:
        summary = await monitor_service.check_all_positions(db)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Global position check failed: {str(e)}"
        )
