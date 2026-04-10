"""
Research API — Trigger and fetch strategy analysis.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Dict

from app.database import get_session
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.agents.strategy_researcher import StrategyResearcher

router = APIRouter(prefix="/research", tags=["research"])

@router.get("/report")
async def get_latest_report(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """
    Generate and return the latest strategy report for the user.
    """
    researcher = StrategyResearcher()
    report = await researcher.generate_weekly_report(session, user.id)
    return report

@router.post("/trigger")
async def trigger_analysis(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Ad-hoc trigger for strategy analysis.
    """
    researcher = StrategyResearcher()
    report = await researcher.generate_weekly_report(session, user.id)
    # Could store this in a 'ResearchReport' model in future phases
    return {"status": "success", "report": report}
