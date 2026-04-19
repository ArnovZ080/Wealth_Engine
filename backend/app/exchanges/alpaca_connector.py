"""
Alpaca Exchange Connector — alpaca-py Implementation with Persistent Client.
"""

from typing import Optional, List
from decimal import Decimal
import datetime

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide as AlpacaSide, TimeInForce, OrderStatus
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

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

class AlpacaConnector(BaseExchangeConnector):
    """
    Alpaca-py based connector for Stocks and ETFs.
    Maintains persistent clients.
    """
    def __init__(self, api_key: str, api_secret: str, is_paper_trading: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.is_paper_trading = is_paper_trading
        
        self.trading_client = TradingClient(api_key, api_secret, paper=is_paper_trading)
        self.data_client = StockHistoricalDataClient(api_key, api_secret)

    async def connect(self) -> bool:
        """Verify credentials."""
        try:
            self.trading_client.get_account()
            return True
        except Exception:
            return False

    async def close(self) -> None:
        """Alpaca clients don't have an async close(), but we provide the method for interface parity."""
        pass

    async def get_balance(self, currency: str = "USD") -> BalanceInfo:
        account = self.trading_client.get_account()
        total = Decimal(str(account.equity))
        available = Decimal(str(account.buying_power))
        return BalanceInfo(total=total, available=available, currency=currency)

    async def get_ticker(self, symbol: str) -> TickerPrice:
        normalized = self.normalize_symbol(symbol)
        # Note: In production, wrap synchronous data_client calls in run_in_executor
        from alpaca.data.requests import StockQuotesRequest
        request_params = StockQuotesRequest(symbol_or_symbols=normalized, timeframe=None)
        quote = self.data_client.get_stock_latest_quote(request_params)[normalized]
        
        return TickerPrice(
            symbol=symbol,
            bid=Decimal(str(quote.bid_price)),
            ask=Decimal(str(quote.ask_price)),
            last=Decimal(str(quote.ask_price)),
            timestamp=quote.timestamp.isoformat()
        )

    async def get_ohlcv(self, symbol: str, timeframe: str, limit: int) -> List[List]:
        normalized = self.normalize_symbol(symbol)
        
        # Mapping timeframe
        tf_map = {
            "1m": TimeFrame.Minute,
            "1h": TimeFrame.Hour,
            "1d": TimeFrame.Day,
        }
        tf = tf_map.get(timeframe, TimeFrame.Hour)
        
        end = datetime.datetime.now(datetime.timezone.utc)
        start = end - datetime.timedelta(days=limit if timeframe == "1d" else (limit // 24) + 1)
        
        request_params = StockBarsRequest(
            symbol_or_symbols=normalized,
            timeframe=tf,
            start=start,
            limit=limit
        )
        bars = self.data_client.get_stock_bars(request_params)[normalized]
        
        ohlcv = []
        for bar in bars:
            ohlcv.append([
                int(bar.timestamp.timestamp() * 1000),
                float(bar.open),
                float(bar.high),
                float(bar.low),
                float(bar.close),
                float(bar.volume)
            ])
        return ohlcv

    async def place_order(self, order: TradeOrder) -> TradeResult:
        normalized = self.normalize_symbol(order.symbol)
        side = AlpacaSide.BUY if order.side == OrderSide.BUY else AlpacaSide.SELL
        
        if order.order_type == OrderType.MARKET:
            req = MarketOrderRequest(
                symbol=normalized,
                qty=float(order.quantity),
                side=side,
                time_in_force=TimeInForce.DAY
            )
        elif order.order_type == OrderType.LIMIT:
            req = LimitOrderRequest(
                symbol=normalized,
                qty=float(order.quantity),
                side=side,
                limit_price=float(order.limit_price),
                time_in_force=TimeInForce.DAY
            )
        else:
            raise ValueError(f"Order type {order.order_type} not supported in Alpaca.")
            
        res = self.trading_client.submit_order(req)
        
        return TradeResult(
            order_id=str(res.id),
            symbol=order.symbol,
            side=order.side,
            filled_quantity=Decimal(str(res.filled_qty or 0)),
            filled_price=Decimal(str(res.filled_avg_price or 0)),
            fees=Decimal("0"),
            fee_currency="USD",
            timestamp=res.created_at.isoformat(),
            raw_response=dict(res)
        )

    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        try:
            self.trading_client.cancel_order_by_id(order_id)
            return True
        except Exception:
            return False

    async def get_open_orders(self, symbol: Optional[str] = None) -> List:
        normalized = self.normalize_symbol(symbol) if symbol else None
        filter = GetOrdersRequest(status=OrderStatus.OPEN, symbols=[normalized] if normalized else None)
        orders = self.trading_client.get_orders(filter)
        return [dict(o) for o in orders]

    async def get_order_status(self, order_id: str, symbol: str) -> dict:
        order = self.trading_client.get_order_by_id(order_id)
        return dict(order)

    def get_supported_assets(self) -> List[AssetClass]:
        return [AssetClass.STOCK, AssetClass.ETF]

    async def get_minimum_order_size(self, symbol: str) -> Decimal:
        return Decimal("0.00001")

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        """
        Alpaca uses symbols like 'AAPL'. 
        Canonical format 'AAPL/USD' or 'AAPL/USDT' should be translated to 'AAPL'.
        """
        if "/" in symbol:
            return symbol.split("/")[0]
        return symbol
