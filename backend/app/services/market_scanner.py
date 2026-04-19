"""
Market Scanner — Identification of BUY/STRONG_BUY opportunities.

Scans watchlists across Binance and Alpaca concurrently using per-exchange semaphores.
"""

import asyncio
import logging
from decimal import Decimal
from dataclasses import dataclass
from typing import List, Dict, Optional

from app.services.indicator_service import IndicatorService, Signal
from app.exchanges.base_connector import BaseExchangeConnector, AssetClass

logger = logging.getLogger(__name__)

@dataclass
class ScanResult:
    symbol: str
    exchange: str              # "binance" or "alpaca"
    asset_class: AssetClass
    signal: Signal
    confidence: float
    indicator_summary: str
    current_price: Decimal
    volume_24h: Optional[Decimal] = None

DEFAULT_WATCHLISTS = {
    "binance": [
        "BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT",
        "XRP/USDT", "ADA/USDT", "DOGE/USDT", "AVAX/USDT",
        "DOT/USDT", "LINK/USDT", "POL/USDT", "ATOM/USDT",
        "UNI/USDT", "LTC/USDT", "NEAR/USDT"
    ],
    "alpaca": [
        "AAPL/USD", "MSFT/USD", "GOOGL/USD", "AMZN/USD", "NVDA/USD", "META/USD",
        "TSLA/USD", "JPM/USD", "V/USD", "JNJ/USD", "WMT/USD", "PG/USD",
        "VOO/USD", "QQQ/USD", "SPY/USD"
    ]
}

class MarketScanner:
    """
    Scans multiple exchanges for trading opportunities.
    """

    def __init__(self, indicator_service: IndicatorService):
        self.indicator_service = indicator_service
        # Per-exchange semaphores: 5 concurrent slots each
        self.semaphores = {
            "binance": asyncio.Semaphore(5),
            "alpaca": asyncio.Semaphore(5)
        }

    async def scan(
        self,
        connectors: Dict[str, BaseExchangeConnector],
        watchlist: Optional[Dict[str, List[str]]] = None
    ) -> List[ScanResult]:
        """
        Scan all symbols across all provided connectors.
        """
        if watchlist is None:
            watchlist = DEFAULT_WATCHLISTS

        tasks = []
        for exchange_name, connector in connectors.items():
            if exchange_name not in watchlist:
                continue
                
            symbols = watchlist[exchange_name]
            for symbol in symbols:
                tasks.append(self._scan_symbol(exchange_name, connector, symbol))

        all_results = await asyncio.gather(*tasks)
        
        # Filter for BUY/STRONG_BUY and sort by confidence
        hits = [r for r in all_results if r and r.signal in [Signal.BUY, Signal.STRONG_BUY]]
        hits.sort(key=lambda x: x.confidence, reverse=True)
        
        return hits

    async def _scan_symbol(self, exchange_name: str, connector: BaseExchangeConnector, symbol: str) -> Optional[ScanResult]:
        """
        Scan a single symbol with rate limiting and semaphore protection.
        """
        # Ensure we don't bombard the API
        sem = self.semaphores.get(exchange_name)
        if not sem:
            # Dynamic semaphore for unknown exchanges
            sem = asyncio.Semaphore(2)
            self.semaphores[exchange_name] = sem

        async with sem:
            try:
                # Per-request delay as per Instruction 200ms
                await asyncio.sleep(0.2)
                
                # 1. Fetch Ticker for price
                ticker = await connector.get_ticker(symbol)
                
                # 2. Run Indicators
                analysis = await self.indicator_service.analyze(connector, symbol)
                
                asset_class = AssetClass.CRYPTO if exchange_name == "binance" else AssetClass.STOCK
                
                return ScanResult(
                    symbol=symbol,
                    exchange=exchange_name,
                    asset_class=asset_class,
                    signal=analysis.signal,
                    confidence=analysis.confidence,
                    indicator_summary=analysis.summary,
                    current_price=ticker.last
                )
            except Exception as e:
                logger.error("Scan failed for %s on %s: %s", symbol, exchange_name, e)
                return None
