"""
Deposit Detector — Automated matching of bank transactions to user deposits.
"""

import logging
import re
from typing import List, Optional
from decimal import Decimal
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.funding import FundingTransaction
from app.services.investec_client import InvestecClient
from app.services.funding_service import FundingService

logger = logging.getLogger(__name__)

class DepositDetector:
    """
    Polls Investec and matches incoming credits to user references.
    """

    def __init__(self):
        self.investec = InvestecClient()
        self.funding_service = FundingService()

    async def scan_for_deposits(self, session: AsyncSession) -> List[FundingTransaction]:
        """
        1. Fetch last 7 days of transactions from Investec.
        2. Identify new CREDIT transactions.
        3. Match against WE-XXXX references.
        4. Credit user balance.
        """
        if not self.investec.is_configured:
            logger.info("Investec not configured. Skipping deposit scan.")
            return []

        # We look back 7 days to ensure we don't miss anything due to lag
        from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        transactions = await self.investec.get_transactions(from_date)
        
        new_deposits = []

        for tx in transactions:
            # We only care about CREDITS (money coming in)
            if tx.get("type") != "CREDIT":
                continue
            
            # Idempotency check: use 'postedOrder' or similar as unique bank ID
            bank_tx_id = tx.get("postedOrder") or tx.get("transactionDate") + "_" + str(tx.get("amount"))
            
            # Check if we already processed this bank transaction
            existing = await session.execute(
                select(FundingTransaction).where(FundingTransaction.bank_transaction_id == bank_tx_id)
            )
            if existing.scalars().first():
                continue

            amount = Decimal(str(tx.get("amount")))
            reference = tx.get("description", "") + " " + tx.get("reference", "")
            
            # Match user via reference
            user = await self._match_reference(reference, session)
            if not user:
                continue
            
            logger.info("Detected new deposit from %s: R%s (Ref: %s)", user.display_name, amount, reference)
            
            try:
                # Use funding service to confirm deposit (handles conversion logic)
                txn = await self.funding_service.confirm_deposit(
                    session, 
                    user.id, 
                    amount, 
                    bank_ref=reference
                )
                # Store the bank transaction ID for idempotency
                txn.bank_transaction_id = bank_tx_id
                
                # Notify via Telegram
                try:
                    from app.services.telegram_service import TelegramService
                    telegram = TelegramService()
                    await telegram.notify_user(user, f"💵 <b>Deposit Confirmed</b>\nAmount: {amount:,.2f} ZAR\nRef: {user.deposit_reference}\nZAR/USDT Rate: {txn.exchange_rate}")
                except Exception as te:
                    logger.error("Failed to send deposit notification: %s", te)
                
                new_deposits.append(txn)
            except Exception as e:
                logger.error("Failed to process auto-deposit: %s", e)

        if new_deposits:
            await session.commit()
            
        return new_deposits

    async def _match_reference(self, reference: str, session: AsyncSession) -> Optional[User]:
        """
        Extract WE-[A-Z]{2,3}\d{4} pattern from string.
        """
        if not reference:
            return None
            
        match = re.search(r'WE-[A-Z]{2,3}\d{4}', reference.upper())
        if not match:
            return None
            
        code = match.group(0)
        res = await session.execute(
            select(User).where(User.deposit_reference == code)
        )
        return res.scalars().first()
