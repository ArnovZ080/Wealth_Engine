"""
Agents API — Adversarial Loop triggering.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.database import get_session
from app.agents.alpha_hunter import AlphaHunter
from app.agents.shadow_agent import ShadowAgent
from app.agents.adversarial_loop import run_adversarial_loop
from app.services.seed_manager import get_seed
from app.config import get_settings

router = APIRouter()
settings = get_settings()

@router.post("/loop/{seed_id}")
async def trigger_adversarial_loop(
    seed_id: str,
    market_data: Dict[str, Any],
    session: AsyncSession = Depends(get_session)
):
    """
    Triggers a Hunter-Shadow loop for a specific seed.
    """
    seed = await get_seed(session, seed_id)
    if not seed:
        raise HTTPException(status_code=404, detail="Seed not found.")
        
    hunter = AlphaHunter(api_key=settings.gemini_api_key or "mock", model=settings.gemini_model)
    shadow = ShadowAgent(api_key=settings.anthropic_api_key or "mock", model=settings.anthropic_model)
    
    decision = await run_adversarial_loop(
        session,
        hunter,
        shadow,
        seed,
        market_data,
        max_rounds=settings.max_refinement_rounds
    )
    
    await session.commit()
    return decision
