"""
Orchestrator API Routes — Triggering the Trading Heartbeat.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.database import get_db
from app.api.deps import get_current_user, get_master_user
from app.models.user import User
from app.services.seed_orchestrator import SeedOrchestrator

router = APIRouter()
orchestrator = SeedOrchestrator()

@router.post("/run-cycle", response_model=Dict[str, Any])
async def run_user_cycle(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger a trading cycle for the current user's forest.
    """
    try:
        summary = await orchestrator.run_cycle(current_user.id, db)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Orchestration cycle failed: {str(e)}"
        )

@router.post("/run-all", response_model=Dict[str, Any])
async def run_global_cycle(
    master_user: User = Depends(get_master_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger a trading cycle for ALL active users. (Master/Admin only)
    """
    try:
        summary = await orchestrator.run_all_users(db)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Global orchestration cycle failed: {str(e)}"
        )
