"""
Heartbeat API endpoints.

POST /api/v1/heartbeat        — Record a user heartbeat (proof-of-life).
GET  /api/v1/heartbeat/status — Check inactivity level and Legacy Protocol status.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import HeartbeatResponse
from app.services.heartbeat import check_inactivity, update_heartbeat

router = APIRouter(prefix="/heartbeat", tags=["heartbeat"])


@router.post(
    "",
    summary="Record Heartbeat",
    description=(
        "Records a user heartbeat timestamp. Resets any Legacy Protocol "
        "trigger if the user returns after 180+ days of inactivity."
    ),
)
async def post_heartbeat(
    session: AsyncSession = Depends(get_db),
):
    """Record a user heartbeat."""
    try:
        timestamp = await update_heartbeat(session)
        return {
            "success": True,
            "heartbeat": timestamp.isoformat(),
            "message": "Heartbeat recorded.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/status",
    response_model=HeartbeatResponse,
    summary="Check Inactivity Status",
    description=(
        "Returns the current inactivity status: NORMAL, WARNING_90, "
        "WARNING_150, or LEGACY_TRIGGER. Includes days since last heartbeat."
    ),
)
async def get_heartbeat_status(
    session: AsyncSession = Depends(get_db),
):
    """Check inactivity level against heartbeat thresholds."""
    try:
        status = await check_inactivity(session)
        return HeartbeatResponse(
            last_heartbeat=status.last_heartbeat,
            days_inactive=status.days_inactive,
            status=status.status,
            message=status.message,
            legacy_triggered=status.legacy_triggered,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
