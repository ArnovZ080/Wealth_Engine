"""
Binance Exchange Connector — CCXT Implementation with Persistent Connection.
"""

import ccxt.async_support as ccxt
from decimal import Decimal
from typing import Optional, List, Any
import datetime

from app.exchanges.base_connector import (
    BaseExchangeConnector,
    BalanceInfo,
    TickerPrice,
    TradeOrder,
    TradeResult,
    AssetClass,
    OrderSide,
    OrderType
)

class BinanceConnector(BaseExchangeConnector):
    """
    CCXT-based connector for Binance.
    Maintains a persistent exchange instance.
    """
    def __init__(self, api_key: str, api_secret: str, is_paper_trading: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.is_paper_trading = is_paper_trading
        
        self.exchange = ccxt.binance({
            "apiKey": self.api_key,
            "secret": self.api_secret,
            "enableRateLimit": True,
        })
        
        if self.is_paper_trading:
            self.exchange.set_sandbox_mode(True)

    async def connect(self) -> bool:
        """Verify credentials."""
        try:
            await self.exchange.fetch_balance()
            return True
        except Exception:
            return False

    async def close(self) -> None:
        """Gracefully close the persistent connection."""
        await self.exchange.close()

    async def get_balance(self, currency: str = "USDT") -> BalanceInfo:
        balances = await self.exchange.fetch_balance()
        total = Decimal(str(balances.get("total", {}).get(currency, 0)))
        free = Decimal(str(balances.get("free", {}).get(currency, 0)))
        return BalanceInfo(total=total, available=free, currency=currency)

    async def get_ticker(self, symbol: str) -> TickerPrice:
        normalized = self.normalize_symbol(symbol)
        ticker = await self.exchange.fetch_ticker(normalized)
        return TickerPrice(
            symbol=symbol,
            bid=Decimal(str(ticker["bid"])),
            ask=Decimal(str(ticker["ask"])),
            last=Decimal(str(ticker["last"])),
            timestamp=ticker["datetime"]
        )

    async def get_ohlcv(self, symbol: str, timeframe: str, limit: int) -> List[List]:
        normalized = self.normalize_symbol(symbol)
        ohlcv = await self.exchange.fetch_ohlcv(normalized, timeframe, limit=limit)
        return ohlcv

    async def place_order(self, order: TradeOrder) -> TradeResult:
        normalized = self.normalize_symbol(order.symbol)
        side = order.side.value # "buy" or "sell"
        type = order.order_type.value # "market" or "limit"
        
        res = await self.exchange.create_order(
            symbol=normalized,
            type=type,
            side=side,
            amount=float(order.quantity),
            price=float(order.limit_price) if order.limit_price else None
        )
        
        return TradeResult(
            order_id=res["id"],
            symbol=order.symbol,
            side=order.side,
            filled_quantity=Decimal(str(res["filled"])),
            filled_price=Decimal(str(res["price"])) if res["price"] else Decimal("0"),
            fees=Decimal("0"), 
            fee_currency="",
            timestamp=res["datetime"],
            raw_response=res
        )

    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        normalized = self.normalize_symbol(symbol)
        try:
            await self.exchange.cancel_order(order_id, normalized)
            return True
        except Exception:
            return False

    async def get_open_orders(self, symbol: Optional[str] = None) -> List:
        normalized = self.normalize_symbol(symbol) if symbol else None
        return await self.exchange.fetch_open_orders(normalized)

    async def get_order_status(self, order_id: str, symbol: str) -> dict:
        normalized = self.normalize_symbol(symbol)
        return await self.exchange.fetch_order(order_id, normalized)

    def get_supported_assets(self) -> List[AssetClass]:
        return [AssetClass.CRYPTO]

    async def get_minimum_order_size(self, symbol: str) -> Decimal:
        normalized = self.normalize_symbol(symbol)
        markets = await self.exchange.load_markets()
        market = markets.get(normalized)
        if market:
            return Decimal(str(market["limits"]["amount"]["min"]))
        return Decimal("0.0001")

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        """
        Binance uses BTC/USDT. Canonical is also BTC/USDT.
        """
        return symbol
