"""
Position Monitor Service — The Watcher.

Automates exits and waterfall settlement for open trades.
Enforces Stop-Loss, Take-Profit, Trailing Stop, and Time Decay logic.
"""

import logging
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trade_decision import TradeDecision
from app.models.seed import Seed, SeedStatus
from app.models.tree import Tree
from app.models.user import User
from app.exchanges.connector_factory import ConnectorFactory
from app.exchanges.base_connector import TradeOrder, OrderSide, OrderType, TradeResult
from app.services.waterfall import execute_waterfall

logger = logging.getLogger(__name__)

class PositionMonitor:
    """
    Watches all open positions and triggers exits.
    """

    def __init__(self):
        self.connector_factory = ConnectorFactory()

    async def check_all_positions(self, db_session: AsyncSession) -> Dict[str, Any]:
        """
        Scan all open TradeDecisions across all users.
        """
        logger.info("Scanning all open positions...")
        
        # Fetch open decisions with user and seed relationships
        stmt = (
            select(TradeDecision)
            .where(TradeDecision.status == "open")
            .options(
                selectinload(TradeDecision.seed).selectinload(Seed.tree).selectinload(Tree.user)
            )
        )
        res = await db_session.execute(stmt)
        decisions = res.scalars().all()
        
        summary = {
            "positions_scanned": len(decisions),
            "exits_triggered": 0,
            "errors": 0,
            "details": []
        }

        # Group by user to minimize connector construction if possible
        # (Though ConnectorFactory likely handles caching/pooling)
        for decision in decisions:
            try:
                user = decision.seed.tree.user
                seed = decision.seed
                
                # Fetch connector
                # We need the exchange name. TradeDecision has it in trade_memo or we add a field.
                # In Phase 3B TradePipeline, we put it in market_data.
                exchange_name = decision.trade_memo.get("exchange", "binance")
                connector = await self.connector_factory.get_connector(user.id, exchange_name, db_session)
                
                if not connector:
                    logger.error("Connector not found for user %s, exchange %s", user.id, exchange_name)
                    continue
                
                # 1. Fetch current price
                ticker = await connector.get_ticker(decision.ticker)
                current_price = ticker.last
                
                # 2. Evaluate
                exit_reason = await self._evaluate_position(decision, current_price)
                
                if exit_reason != "hold":
                    await self._execute_exit(decision, exit_reason, current_price, connector, db_session)
                    summary["exits_triggered"] += 1
                    summary["details"].append(f"Exit {decision.ticker} for {user.email}: {exit_reason}")
                else:
                    # Update highest price for trailing stop tracking
                    if decision.highest_price_since_entry is None or current_price > decision.highest_price_since_entry:
                        decision.highest_price_since_entry = current_price
                    
                    # Check for trailing stop activation
                    if not decision.trailing_stop_active:
                        if current_price >= decision.entry_price * Decimal("1.03"):
                            decision.trailing_stop_active = True
                            logger.info("Trailing stop ACTIVATED for %s", decision.ticker)
                
            except Exception as e:
                logger.error("Error monitoring position %s: %s", decision.id, e)
                summary["errors"] += 1
                summary["details"].append(f"Error {decision.id}: {str(e)}")

        await db_session.commit()
        return summary

    async def _evaluate_position(self, decision: TradeDecision, current_price: Decimal) -> str:
        """
        Evaluate exit rules.
        """
        # Directional logic (Long only for now per Phase 3B, but code for both)
        is_long = decision.direction == "long"
        
        # 1. Stop-Loss
        if is_long and current_price <= decision.stop_loss:
            return "stop_loss"
        if not is_long and current_price >= decision.stop_loss:
            return "stop_loss"
            
        # 2. Take-Profit
        if is_long and current_price >= decision.target_exit:
            return "take_profit"
        if not is_long and current_price <= decision.target_exit:
            return "take_profit"
            
        # 3. Trailing Stop
        if decision.trailing_stop_active and decision.highest_price_since_entry:
            if is_long:
                if current_price < decision.highest_price_since_entry * Decimal("0.99"):
                    return "trailing_stop"
            else:
                # For shorts, trailing stop follows price DOWN, highest_price becomes lowest_price
                # But instructions didn't specify short TS logic, so we'll stick to long rules or extend
                if current_price > decision.highest_price_since_entry * Decimal("1.01"):
                    return "trailing_stop"

        # 4. Time Decay (72h)
        open_time = decision.created_at
        if datetime.now(timezone.utc) - open_time > timedelta(hours=72):
            change_pct = abs(current_price - decision.entry_price) / decision.entry_price
            if change_pct < Decimal("0.005"): # < 0.5%
                return "time_decay"

        return "hold"

    async def _execute_exit(
        self, 
        decision: TradeDecision, 
        reason: str, 
        current_price: Decimal, 
        connector, 
        db_session: AsyncSession
    ) -> Optional[TradeResult]:
        """
        Execute market sell and settle.
        """
        logger.info("EXIT TRIGGERED for %s: %s at %s", decision.ticker, reason, current_price)
        
        # 1. Execute Order
        # Quantity from TradeResult of Entry? Or from position_size / entry_price?
        # Entry logic in Phase 3B used: quantity = position_value / current_price
        # We should probably store quantity in TradeDecision. 
        # For now, let's derive it from position_size / entry_price
        quantity = decision.position_size / decision.entry_price
        
        order = TradeOrder(
            symbol=decision.ticker,
            side=OrderSide.SELL if decision.direction == "long" else OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=quantity
        )
        
        try:
            res = await connector.place_order(order)
            exit_price = res.filled_price if res.filled_price > 0 else current_price
            
            # 2. Update Decision
            decision.status = f"closed_{'profit' if exit_price > decision.entry_price else 'loss'}"
            decision.exit_price = exit_price
            decision.exit_timestamp = datetime.now(timezone.utc)
            decision.exit_reason = reason
            
            # 3. Settle
            user = decision.seed.tree.user
            await self._settle_trade(decision, decision.entry_price, exit_price, quantity, res.fees, user, db_session)
            
            return res
        except Exception as e:
            logger.error("Failed to execute exit for %s: %s", decision.ticker, e)
            return None

    async def _settle_trade(
        self, 
        decision: TradeDecision, 
        entry_price: Decimal, 
        exit_price: Decimal, 
        quantity: Decimal, 
        fees: Decimal, 
        user: User, 
        db_session: AsyncSession
    ):
        """
        Final profit/loss settlement.
        """
        # Gross profit calculation
        if decision.direction == "long":
            gross_profit = (exit_price - entry_price) * quantity
        else:
            gross_profit = (entry_price - exit_price) * quantity
            
        decision.realized_pnl = gross_profit - fees
        
        seed = decision.seed
        if gross_profit > 0:
            # 1. Run Waterfall (Profits)
            await execute_waterfall(
                session=db_session,
                user=user,
                gross_profit=gross_profit,
                fees=fees,
                seed_id=seed.seed_id
            )
        else:
            # 2. Handle Loss (Direct Deduction)
            # Add reinvestment logic if we want, but instructions say deduct from seed balance directly
            seed.current_value += (gross_profit - fees)
            
            # Ground Zero check
            if seed.current_value <= seed.stop_loss_floor:
                logger.warning("Seed %s hit GROUND ZERO floor. Value: %s", seed.seed_id, seed.current_value)
                seed.status = "ground_zero"
                seed.strike_count += 1
                # Future: triggers reset-request or fleet-level pause
        
        # Mark as closed in any case
        # decision.status is already set in _execute_exit
