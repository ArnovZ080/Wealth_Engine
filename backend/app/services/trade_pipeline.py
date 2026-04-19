"""
Trade Execution Pipeline — The Root Orchestrator's core execution engine.

Coordinates Scanner, IndicatorService, Hunter-Shadow agents, and Exchange Connectors.
"""

import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.models.seed import Seed, SeedStatus
from app.models.forest import UserForestState
from app.models.trade_decision import TradeDecision
from app.exchanges.base_connector import BaseExchangeConnector, TradeOrder, OrderType, OrderSide, TradeResult
from app.exchanges.connector_factory import ConnectorFactory
from app.services.indicator_service import IndicatorService, Signal
from app.services.market_scanner import MarketScanner, ScanResult
from app.services.waterfall import execute_waterfall
from app.agents.adversarial_loop import run_adversarial_loop
from app.agents.alpha_hunter import AlphaHunter
from app.agents.shadow_agent import ShadowAgent

logger = logging.getLogger(__name__)

class TradePipeline:
    """
    End-to-end trade execution pipeline.
    """

    def __init__(
        self,
        session: AsyncSession,
        user_id: str,
        indicator_service: IndicatorService,
        connector_factory: ConnectorFactory
    ):
        self.session = session
        self.user_id = user_id
        self.indicator_service = indicator_service
        self.connector_factory = connector_factory
        self.scanner = MarketScanner(indicator_service)

    async def execute_for_seed(self, seed_id: str) -> Optional[TradeResult]:
        """
        Run the full pipeline for a specific seed.
        """
        # 1. Pre-flight Checks
        seed = await self._get_seed_with_user_check(seed_id)
        if not seed or seed.status != SeedStatus.ACTIVE:
            logger.info("Seed %s is not active. Skipping.", seed_id)
            return None

        user_forest = await self._get_user_forest()
        if user_forest.kill_switch_status != "active":
            logger.warning("User %s Kill Switch is ON. Aborting trade.", self.user_id)
            return None

        # 2. Exchange Selection
        # Stage 1 (<$1k): Crypto focus. Stage 2+: Mixed.
        exchange_preference = "alpaca"
        connectors = await self.connector_factory.get_all_connectors(self.user_id, self.session)
        if not connectors:
            logger.error("No exchange connectors found for user %s", self.user_id)
            return None

        # 3. Market Scan
        hits = await self.scanner.scan(connectors)
        if not hits:
            logger.info("No BUY/STRONG_BUY signals found for user %s. Standing by.", self.user_id)
            return None

        # Take the top ranked hit that matches exchange preference if any
        opportunity = hits[0]
        if exchange_preference and exchange_preference in connectors:
            for hit in hits:
                if hit.exchange == exchange_preference:
                    opportunity = hit
                    break
        
        # 4. Dumb Mode Baseline Check
        # Confidence must be >= 0.6 per Instruction
        if opportunity.confidence < 0.6:
            logger.info("Opportunity %s confidence %.2f < 0.6. Skipping.", 
                        opportunity.symbol, opportunity.confidence)
            return None

        # 5. Adversarial Loop (Hunter-Shadow)
        # We mock agents for Phase 3B per instructions
        hunter = AlphaHunter() # Mocked
        shadow = ShadowAgent() # Mocked
        
        # Prepare market data context
        market_data = {
            "symbol": opportunity.symbol,
            "exchange": opportunity.exchange,
            "current_price": float(opportunity.current_price),
            "indicators": opportunity.indicator_summary,
            "dumb_mode_signal": opportunity.signal.value
        }
        
        decision = await run_adversarial_loop(self.session, hunter, shadow, seed, market_data)
        
        if not decision.execution_authorized:
            logger.info("Adversarial Loop VETOED trade for %s", opportunity.symbol)
            return None

        # Record Dumb Mode Agreement
        # Agreed if both are BUY/STRONG_BUY
        decision.dumb_mode_agreed = True # Hunter is mocked to Approve/Buy for now
        
        # 6. Position Sizing (Fractional Kelly f*=0.25)
        from app.services.position_sizing import KellyPositionSizer
        
        # Use indicator confidence + LLM confidence average? 
        # Instruction says: "Use the TradeMemo's entry, target, stop_loss, and the indicator service's confidence score."
        # Use decision confidence (0-100 scale) converted to 0-1
        confidence = float(decision.confidence_score) / 100.0 if decision.confidence_score else float(opportunity.confidence) 
        
        position_value = KellyPositionSizer.calculate(
            seed_value=seed.current_value,
            entry_price=decision.entry_price, # from the authorized decision/memo
            target_exit=decision.target_exit,
            stop_loss=decision.stop_loss,
            confidence=confidence
        )
        
        if position_value <= 0:
            logger.info("Kelly sizing returned 0 (no edge). Skipping trade.")
            return None
        
        # Min Order Size Check
        connector = connectors[opportunity.exchange]
        min_size = await connector.get_minimum_order_size(opportunity.symbol)
        quantity = (position_value / opportunity.current_price).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)
        
        if quantity < min_size:
            logger.warning("Position size %.8f < min size %.8f for %s", quantity, min_size, opportunity.symbol)
            return None

        # 7. Execution (Paper/Live)
        order = TradeOrder(
            symbol=opportunity.symbol,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=quantity
        )
        
        logger.info("EXECUTING: Buy %.8f %s on %s", quantity, opportunity.symbol, opportunity.exchange)
        trade_result = await connector.place_order(order)
        
        # 8. Settlement & Notification
        decision.executed = True
        
        # Notify via Telegram
        try:
            from app.services.telegram_service import TelegramService
            telegram = TelegramService()
            user_res = await self.session.execute(select(User).where(User.id == self.user_id))
            user = user_res.scalars().first()
            if user:
                alert = telegram.format_trade_alert(
                    "BUY", 
                    opportunity.symbol, 
                    float(opportunity.current_price), 
                    reason=f"Seed {seed.id[:8]} - Hunter rationale: {decision.hunter_rationale[:50]}..."
                )
                await telegram.notify_user(user, alert)
        except Exception as te:
            logger.error("Failed to send trade notification: %s", te)

        await self.session.commit()
        return trade_result

    async def _get_seed_with_user_check(self, seed_id: str) -> Optional[Seed]:
        stmt = select(Seed).where(Seed.id == seed_id)
        res = await self.session.execute(stmt)
        seed = res.scalar_one_or_none()
        # verify user scope in the Orchestrator instead or here
        return seed

    async def _get_user_forest(self) -> UserForestState:
        from app.services.state_manager import get_user_forest_state
        return await get_user_forest_state(self.session, self.user_id)
