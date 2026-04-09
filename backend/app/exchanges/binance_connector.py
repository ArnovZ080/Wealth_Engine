"""
Binance Exchange Connector — CCXT Implementation.
"""

import ccxt.async_support as ccxt
from decimal import Decimal
from typing import Optional, List
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
        try:
            await self.exchange.fetch_balance()
            return True
        except Exception:
            return False
        finally:
            await self.exchange.close()

    async def get_balance(self, currency: str = "USDT") -> BalanceInfo:
        exchange = ccxt.binance({
            "apiKey": self.api_key,
            "secret": self.api_secret,
            "enableRateLimit": True,
        })
        if self.is_paper_trading:
            exchange.set_sandbox_mode(True)
        try:
            balances = await exchange.fetch_balance()
            total = Decimal(str(balances.get("total", {}).get(currency, 0)))
            free = Decimal(str(balances.get("free", {}).get(currency, 0)))
            return BalanceInfo(total=total, available=free, currency=currency)
        finally:
            await exchange.close()

    async def get_ticker(self, symbol: str) -> TickerPrice:
        # ccxt uses symbols like BTC/USDT
        exchange = ccxt.binance({"enableRateLimit": True})
        if self.is_paper_trading:
            exchange.set_sandbox_mode(True)
        try:
            ticker = await exchange.fetch_ticker(symbol)
            return TickerPrice(
                symbol=symbol,
                bid=Decimal(str(ticker["bid"])),
                ask=Decimal(str(ticker["ask"])),
                last=Decimal(str(ticker["last"])),
                timestamp=ticker["datetime"]
            )
        finally:
            await exchange.close()

    async def place_order(self, order: TradeOrder) -> TradeResult:
        exchange = ccxt.binance({
            "apiKey": self.api_key,
            "secret": self.api_secret,
            "enableRateLimit": True,
        })
        if self.is_paper_trading:
            exchange.set_sandbox_mode(True)
        try:
            side = order.side # "buy" or "sell"
            type = order.order_type # "market" or "limit"
            
            res = await exchange.create_order(
                symbol=order.symbol,
                type=type,
                side=side,
                amount=float(order.quantity),
                price=float(order.limit_price) if order.limit_price else None
            )
            
            return TradeResult(
                order_id=res["id"],
                symbol=res["symbol"],
                side=OrderSide(res["side"]),
                filled_quantity=Decimal(str(res["filled"])),
                filled_price=Decimal(str(res["price"])) if res["price"] else Decimal("0"),
                fees=Decimal("0"), # Binance fees often complex in CCXT, handled in post-analysis
                fee_currency="",
                timestamp=res["datetime"],
                raw_response=res
            )
        finally:
            await exchange.close()

    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        exchange = ccxt.binance({
            "apiKey": self.api_key,
            "secret": self.api_secret,
            "enableRateLimit": True,
        })
        if self.is_paper_trading:
            exchange.set_sandbox_mode(True)
        try:
            await exchange.cancel_order(order_id, symbol)
            return True
        except Exception:
            return False
        finally:
            await exchange.close()

    async def get_open_orders(self, symbol: Optional[str] = None) -> List:
        exchange = ccxt.binance({
            "apiKey": self.api_key,
            "secret": self.api_secret,
            "enableRateLimit": True,
        })
        if self.is_paper_trading:
            exchange.set_sandbox_mode(True)
        try:
            return await exchange.fetch_open_orders(symbol)
        finally:
            await exchange.close()

    async def get_order_status(self, order_id: str, symbol: str) -> dict:
        exchange = ccxt.binance({
            "apiKey": self.api_key,
            "secret": self.api_secret,
            "enableRateLimit": True,
        })
        if self.is_paper_trading:
            exchange.set_sandbox_mode(True)
        try:
            return await exchange.fetch_order(order_id, symbol)
        finally:
            await exchange.close()

    def get_supported_assets(self) -> List[AssetClass]:
        return [AssetClass.CRYPTO]

    async def get_minimum_order_size(self, symbol: str) -> Decimal:
        exchange = ccxt.binance({"enableRateLimit": True})
        try:
            markets = await exchange.load_markets()
            market = markets.get(symbol)
            if market:
                return Decimal(str(market["limits"]["amount"]["min"]))
            return Decimal("0.0001")
        finally:
            await exchange.close()
