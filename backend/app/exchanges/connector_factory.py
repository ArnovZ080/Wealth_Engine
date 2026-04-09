"""
Connector Factory — Instantiates exchange connectors from DB credentials.
"""

import logging
from typing import Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exchange_credential import ExchangeCredential
from app.services.crypto_service import decrypt
from app.exchanges.base_connector import BaseExchangeConnector
from app.exchanges.binance_connector import BinanceConnector
from app.exchanges.alpaca_connector import AlpacaConnector

logger = logging.getLogger(__name__)

class ConnectorFactory:
    """
    Creates exchange connectors for a specific user by loading
    their encrypted credentials from the database.
    """

    @staticmethod
    async def get_connector(user_id: str, exchange: str, session: AsyncSession) -> BaseExchangeConnector:
        """
        Load user's credentials, decrypt them, and return an initialized connector.
        Raises ValueError if no credentials found for that exchange.
        """
        stmt = select(ExchangeCredential).where(
            ExchangeCredential.user_id == user_id,
            ExchangeCredential.exchange == exchange,
            ExchangeCredential.is_active == True
        )
        result = await session.execute(stmt)
        credential = result.scalar_one_or_none()
        
        if not credential:
            raise ValueError(f"No active credentials found for {exchange}")

        # Decrypt keys
        api_key = decrypt(credential.api_key_encrypted)
        api_secret = decrypt(credential.api_secret_encrypted)

        if exchange.lower() == "binance":
            connector = BinanceConnector(
                api_key=api_key,
                api_secret=api_secret,
                is_paper_trading=credential.is_paper_trading
            )
        elif exchange.lower() == "alpaca":
            connector = AlpacaConnector(
                api_key=api_key,
                api_secret=api_secret,
                is_paper_trading=credential.is_paper_trading
            )
        else:
            raise ValueError(f"Unsupported exchange type: {exchange}")

        # Basic connection test
        await connector.connect()
        return connector

    @staticmethod
    async def get_all_connectors(user_id: str, session: AsyncSession) -> Dict[str, BaseExchangeConnector]:
        """
        Return a dict of all active connectors for a user.
        """
        stmt = select(ExchangeCredential).where(
            ExchangeCredential.user_id == user_id,
            ExchangeCredential.is_active == True
        )
        result = await session.execute(stmt)
        credentials = result.scalars().all()
        
        connectors = {}
        for cred in credentials:
            try:
                conn = await ConnectorFactory.get_connector(user_id, cred.exchange, session)
                connectors[cred.exchange] = conn
            except Exception as e:
                logger.warning(f"Failed to initialize {cred.exchange} for user {user_id}: {e}")
        
        return connectors
