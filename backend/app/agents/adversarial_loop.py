"""
Adversarial Loop — The Hunter-Shadow Pipeline.

Coordinates Gemini 3.1 and Claude 4.6 Opus in a multi-round refinement loop.
"""

import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.alpha_hunter import AlphaHunter, TradeMemo
from app.agents.shadow_agent import ShadowAgent, ShadowVerdict
from app.models.trade_decision import TradeDecision
from app.models.seed import Seed

logger = logging.getLogger(__name__)

async def run_adversarial_loop(
    session: AsyncSession,
    hunter: AlphaHunter,
    shadow: ShadowAgent,
    seed: Seed,
    market_data: Dict[str, Any],
    max_rounds: int = 3
) -> TradeDecision:
    """
    Executes the Hunter-Shadow loop.
    
    1. Hunter proposes.
    2. Shadow reviews.
    3. If REFINE, Hunter adjusts (up to max_rounds).
    4. Persists the result to trade_decisions.
    """
    round_num = 0
    current_memo: Optional[TradeMemo] = None
    verdict: Optional[ShadowVerdict] = None
    adversarial_log = []

    # Context for agents
    seed_context = {
        "seed_id": seed.seed_id,
        "current_value": seed.current_value,
        "strategy": seed.strategy
    }

    while round_num < max_rounds:
        round_num += 1
        logger.info("Adversarial Loop Round %s for seed %s", round_num, seed.seed_id)

        # 1. Hunter Proposes (or refines based on previous shadow feedback)
        # In a real impl, we'd pass the previous shadow_verdict to the hunter
        current_memo = await hunter.generate_proposal(market_data, seed_context)
        
        # 2. Shadow Reviews
        verdict = await shadow.review_proposal(current_memo)
        
        adversarial_log.append({
            "round": round_num,
            "memo": current_memo.model_dump(),
            "verdict": verdict.model_dump()
        })

        if verdict.decision == "APPROVE":
            logger.info("Trade APPROVED by Shadow in round %s", round_num)
            break
        elif verdict.decision == "VETO":
            logger.warning("Trade VETOED by Shadow in round %s", round_num)
            break
        elif verdict.decision == "REFINE":
            logger.info("Shadow requested REFINE in round %s. Flaws: %s", round_num, verdict.flaws_found)
            if round_num >= max_rounds:
                logger.warning("Max refinement rounds reached. Opportunity Decay — Killing trade.")
                break
            # Preparation for next round: update context or market_data if needed
            continue

    # 3. Final decision logic
    # Confidence threshold (e.g., 85) check
    execution_authorized = False
    if verdict and verdict.decision == "APPROVE" and current_memo and current_memo.confidence >= 85:
        execution_authorized = True

    # 4. Persistence
    decision_record = TradeDecision(
        seed_id=seed.id,
        ticker=current_memo.ticker,
        direction=current_memo.direction,
        entry_price=current_memo.entry_price,
        target_exit=current_memo.target_exit,
        stop_loss=current_memo.stop_loss,
        position_size=current_memo.position_size,
        confidence_score=current_memo.confidence,
        hunter_rationale=current_memo.rationale,
        shadow_verdict=verdict.decision,
        shadow_flaws=verdict.flaws_found,
        refinement_rounds=round_num,
        execution_authorized=execution_authorized,
        trade_memo=current_memo.model_dump(),
        adversarial_log={"rounds": adversarial_log}
    )
    session.add(decision_record)
    
    # Update seed last trade timestamp
    seed.last_trade_at = datetime.now(timezone.utc)
    seed.confidence_score = float(current_memo.confidence)

    logger.info("Trade decision persisted. Authorized: %s, Verdict: %s", 
                execution_authorized, verdict.decision)
    
    return decision_record
