"""
Cash-Out Service — Implements the Anytime Cash-Out hierarchical liquidation protocol.

Matches Master Document §10.1.
"""

import logging
from decimal import Decimal
from datetime import datetime, timezone
from typing import Dict, Any, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.forest import UserForestState
from app.models.funding import FundingTransaction
from app.models.user import User

logger = logging.getLogger(__name__)

class CashOutService:
    """
    Handles hierarchical liquidation of assets for user withdrawals.
    """

    async def preview_withdrawal(self, session: AsyncSession, user_id: str, amount_zar: Decimal) -> Dict[str, Any]:
        """
        Calculate which tiers will be drawn and how much from each, WITHOUT executing.
        Assumes ZAR/USDT conversion for calculations.
        """
        # Fetch forest state
        res = await session.execute(select(UserForestState).where(UserForestState.user_id == user_id))
        forest = res.scalars().first()
        if not forest:
            raise ValueError(f"Forest state for user {user_id} not found.")

        # For preview, we currently use a "representative" rate to show the breakdown in ZAR.
        # But balances are in USDT. So we convert requested ZAR to USDT first.
        # MVP: use 19.0 for preview calculations.
        rate = Decimal("19.0")
        requested_usdt = amount_zar / rate
        
        remaining = requested_usdt
        breakdown = []

        # 1. Reservoir (BUIDL) - Instant
        res_bal = forest.shared_reservoir_balance
        if res_bal > 0 and remaining > 0:
            draw = min(remaining, res_bal)
            breakdown.append({
                "source": "Reservoir (BUIDL)",
                "amount_usdt": draw,
                "amount_zar_approx": draw * rate,
                "settlement": "Instant"
            })
            remaining -= draw

        # 2. Nursery (USDC) - Instant
        nur_bal = forest.shared_nursery_balance
        if nur_bal > 0 and remaining > 0:
            draw = min(remaining, nur_bal)
            breakdown.append({
                "source": "Nursery (USDC)",
                "amount_usdt": draw,
                "amount_zar_approx": draw * rate,
                "settlement": "Instant"
            })
            remaining -= draw

        # 3. Vault Tier 2 (ETFs) - 1-2 Days
        v2_bal = forest.vault_tier2_etfs
        if v2_bal > 0 and remaining > 0:
            draw = min(remaining, v2_bal)
            breakdown.append({
                "source": "Vault Tier 2 (ETFs)",
                "amount_usdt": draw,
                "amount_zar_approx": draw * rate,
                "settlement": "1-2 business days"
            })
            remaining -= draw

        # 4. Vault Tier 3 (Real Estate) - 3-10 Days
        v3_bal = forest.vault_tier3_realestate
        if v3_bal > 0 and remaining > 0:
            draw = min(remaining, v3_bal)
            breakdown.append({
                "source": "Vault Tier 3 (Real Estate)",
                "amount_usdt": draw,
                "amount_zar_approx": draw * rate,
                "settlement": "3-10 business days"
            })
            remaining -= draw

        # 5. Active Seeds - Last Resort
        if remaining > 0:
            breakdown.append({
                "source": "Active Seeds (LAST RESORT)",
                "amount_usdt": remaining,
                "amount_zar_approx": remaining * rate,
                "settlement": "Immediate - closes live positions",
                "warning": True
            })

        return {
            "requested_zar": amount_zar,
            "target_usdt": requested_usdt,
            "fulfillable_usdt": requested_usdt - remaining,
            "shortfall_usdt": remaining,
            "breakdown": breakdown
        }

    async def execute_withdrawal(self, session: AsyncSession, user_id: str, amount_zar: Decimal) -> FundingTransaction:
        """
        Execute hierarchical liquidation and create a pending FundingTransaction.
        """
        preview = await self.preview_withdrawal(session, user_id, amount_zar)
        
        # Fetch forest and lock for update
        res = await session.execute(
            select(UserForestState).where(UserForestState.user_id == user_id).with_for_update()
        )
        forest = res.scalars().first()
        
        # Deduct from balances based on breakdown
        for item in preview["breakdown"]:
            source = item["source"]
            amount = item["amount_usdt"]
            
            if source == "Reservoir (BUIDL)":
                forest.shared_reservoir_balance -= amount
            elif source == "Nursery (USDC)":
                forest.shared_nursery_balance -= amount
            elif source == "Vault Tier 2 (ETFs)":
                forest.vault_tier2_etfs -= amount
            elif source == "Vault Tier 3 (Real Estate)":
                forest.vault_tier3_realestate -= amount
            elif source == "Active Seeds (LAST RESORT)":
                # Implementation of closing seeds is a complex Phase 5 item.
                # For Phase 4, we log it and proceed with the fulfillable portion if allowed.
                logger.warning("Withdrawal requires seed liquidation. Support coming in Phase 5.")
                # We'll still record the request.

        # Create Transaction record
        user_res = await session.execute(select(User).where(User.id == user_id))
        user = user_res.scalars().first()
        
        tx = FundingTransaction(
            user_id=user_id,
            type="withdrawal",
            amount_zar=amount_zar,
            status="pending",
            reference_code=user.deposit_reference or "N/A",
            notes=f"Liquidation breakdown: {preview['breakdown']}"
        )
        session.add(tx)
        await session.commit()
        return tx
