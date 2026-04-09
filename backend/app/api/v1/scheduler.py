"""
Scheduler API Routes — Monitoring for background tasks.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from app.api.deps import get_master_user
from app.models.user import User
from app.services.scheduler import get_scheduler

router = APIRouter()

@router.get("/status", response_model=Dict[str, Any])
async def get_scheduler_status(
    master_user: User = Depends(get_master_user)
):
    """
    Check the status and health of background task loops (Master only).
    """
    try:
        scheduler = get_scheduler()
        return await scheduler.get_status()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch scheduler status: {str(e)}"
        )

@router.post("/toggle", response_model=Dict[str, Any])
async def toggle_scheduler(
    enabled: bool,
    master_user: User = Depends(get_master_user)
):
    """
    Enable or disable the scheduler dynamically (Master only).
    """
    try:
        scheduler = get_scheduler()
        if enabled:
            await scheduler.start()
        else:
            await scheduler.stop()
        return {"success": True, "enabled": scheduler.enabled, "running": scheduler.running}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle scheduler: {str(e)}"
        )
