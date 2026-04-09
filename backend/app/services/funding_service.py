"""
Funding Service — Handles deposit recognition, conversion, and allocation.
"""

import logging
import random
import string
from decimal import Decimal
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.user import User
from app.models.funding import FundingTransaction
from app.models.forest import UserForestState
from app.exchanges.connector_factory import ConnectorFactory

logger = logging.getLogger(__name__)
settings = get_settings()

class FundingService:
    """
    Manages the lifecycle of ZAR deposits and their conversion to USDT.
    """

    async def generate_deposit_reference(self, session: AsyncSession, user: User) -> str:
        """
        Generate a unique, permanent deposit reference for the user.
        Format: WE-{INITIALS}{4-digit-ID} e.g., WE-ARN0042
        """
        if user.deposit_reference:
            return user.deposit_reference

        # Get initials or initials from email if display_name is short
        initials = "".join([n[0] for n in user.display_name.split() if n])[:3].upper()
        if not initials:
            initials = user.email[:2].upper()

        # Simple increment or random for MVP
        # For actual production, we want this to be unique and consistent.
        # Here we'll just use a random 4-digit suffix for now, but ensure uniqueness.
        while True:
            digits = "".join(random.choices(string.digits, k=4))
            ref = f"WE-{initials}{digits}"
            
            # Check for collision
            res = await session.execute(select(User).where(User.deposit_reference == ref))
            if not res.scalars().first():
                user.deposit_reference = ref
                await session.commit()
                return ref

    async def get_deposit_instructions(self, user: User) -> dict:
        """
        Return the banking details and unique reference for the user.
        """
        return {
            "bank_name": "Investec Bank",
            "account_holder": "Wealth Engine (Pty) Ltd",
            "account_number": getattr(settings, "INVESTEC_ACCOUNT_NUMBER", "123456789"),
            "branch_code": getattr(settings, "INVESTEC_BRANCH_CODE", "580105"),
            "reference": user.deposit_reference,
            "instructions": (
                "Use your unique reference code as the payment reference. "
                "Deposits are typically confirmed within 1-2 business days."
            ),
        }

    async def confirm_deposit(
        self, session: AsyncSession, user_id: str, amount_zar: Decimal, bank_ref: Optional[str] = None
    ) -> FundingTransaction:
        """
        Master manually confirms a deposit has been received.
        1. Fetch real-time USDT/ZAR rate from Binance.
        2. Calculate USDT amount.
        3. Update UserForestState (Reservoir balance).
        4. Record transaction.
        """
        user_res = await session.execute(select(User).where(User.id == user_id))
        user = user_res.scalars().first()
        if not user:
            raise ValueError(f"User {user_id} not found.")

        # 1. Fetch real-time rate
        exchange_rate = Decimal("19.00") # Default fallback
        manual_review = False
        exchange_amount = Decimal("0")
        
        try:
            # Note: CCXT Binance might not have a direct USDT/ZAR orderbook for all methods.
            # We typically fetch ZAR/USDT or USDT/ZAR depending on availability.
            # ccxt.binance() get_ticker('USDT/ZAR')
            connector = ConnectorFactory.get_connector("binance", "master_keys_mock") # we use any key to check public ticker
            ticker = await connector.get_ticker("USDT/ZAR")
            if ticker and "last" in ticker:
                exchange_rate = Decimal(str(ticker["last"]))
            else:
                logger.warning("Could not fetch real-time USDT/ZAR. Falling back to default.")
                manual_review = True
        except Exception as e:
            logger.error("Error fetching conversion rate: %s", e)
            exchange_rate = getattr(settings, "DEFAULT_ZAR_USD_RATE", Decimal("19.0"))
            manual_review = True

        # 2. Calculate USDT
        # ZAR / Rate = USDT (e.g. 1900 ZAR / 19.0 = 100 USDT)
        exchange_amount = (amount_zar / exchange_rate).quantize(Decimal("1.00000000"))

        # 3. Create Transaction record
        tx = FundingTransaction(
            user_id=user_id,
            type="deposit",
            amount_zar=amount_zar,
            exchange_rate=exchange_rate,
            exchange_amount=exchange_amount,
            status="credited",
            reference_code=user.deposit_reference,
            bank_reference=bank_ref,
            manual_review_flag=manual_review,
            completed_at=datetime.now(timezone.utc),
        )
        session.add(tx)

        # 4. Credit UserForestState (Phase 4 Logic: Deposits go to Reservoir / BUIDL)
        # Actually, in the waterfall, new money is effectively the "Nursery" ready-fund 
        # but the prompt says: "confirm a pending deposit... System credits the user's internal balance...
        # and "Waterfall settlement service for profits and deducts losses directly from Seed balances".
        # Master Doc §10.1: "Reservoir (BUIDL)... Nursery (USDC)".
        # For Phase 4, we'll credit the shared_reservoir_balance (BUIDL) as it is the "T1: instant" source.
        
        forest_res = await session.execute(select(UserForestState).where(UserForestState.user_id == user_id))
        forest = forest_res.scalars().first()
        if forest:
            forest.shared_reservoir_balance += exchange_amount
            logger.info("Credited %s USDT to user %s reservoir.", exchange_amount, user_id)
        
        await session.commit()
        return tx

    async def get_user_transactions(self, session: AsyncSession, user_id: str) -> List[FundingTransaction]:
        """Fetch transaction history for a user."""
        res = await session.execute(
            select(FundingTransaction)
            .where(FundingTransaction.user_id == user_id)
            .order_by(FundingTransaction.created_at.desc())
        )
        return res.scalars().all()
