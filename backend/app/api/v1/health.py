"""
Health Check API — System vitals and core component status.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
import time

from app.database import get_session
from app.config import get_settings

router = APIRouter(prefix="/health", tags=["health"])
settings = get_settings()

@router.get("")
async def health_check(session: AsyncSession = Depends(get_session)) -> Dict[str, Any]:
    """
    Returns the status of the database and core services.
    """
    start_time = time.time()
    
    # 1. Database Check
    db_status = "ok"
    try:
        await session.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # 2. Config Check (Basic)
    config_status = "ok"
    if not getattr(settings, "JWT_SECRET_KEY", None):
        config_status = "error: JWT_SECRET_KEY missing"

    return {
        "status": "unhealthy" if "error" in db_status or "error" in config_status else "healthy",
        "database": db_status,
        "config": config_status,
        "version": "1.0.0-phase5",
        "latency_ms": round((time.time() - start_time) * 1000, 2)
    }
