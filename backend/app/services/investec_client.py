"""
Investec API Client — Stub for Phase 4.

Full integration with Investec Programmable Banking scheduled for Phase 5.
"""

import logging
from decimal import Decimal
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class InvestecClient:
    """
    Stub client for Investec API.
    Used for reading transactions and making payouts.
    """

    def __init__(self, client_id: str, client_secret: str, account_id: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.account_id = account_id

    async def get_recent_transactions(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Fetch recent transactions.
        Stub: Returns an empty list.
        """
        logger.info("Investec stub: fetching recent transactions.")
        return []

    async def make_payment(
        self, beneficiary_account: str, amount: Decimal, reference: str
    ) -> Dict[str, Any]:
        """
        Send EFT payment to a beneficiary.
        Stub: Logs the request and returns a mock success.
        """
        logger.info(
            "Investec stub: Processing payment of %s ZAR to %s (Ref: %s)",
            amount, beneficiary_account, reference
        )
        return {"success": True, "transaction_id": "MOCK-INV-123", "status": "processing"}
