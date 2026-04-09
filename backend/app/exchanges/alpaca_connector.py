"""
Alpaca Exchange Connector — alpaca-py Implementation.
"""

from typing import Optional, List
from decimal import Decimal
import datetime

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide as AlpacaSide, TimeInForce, OrderStatus
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockQuotesRequest

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
    """
    def __init__(self, api_key: str, api_secret: str, is_paper_trading: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.is_paper_trading = is_paper_trading
        self.trading_client = TradingClient(api_key, api_secret, paper=is_paper_trading)
        self.data_client = StockHistoricalDataClient(api_key, api_secret)

    async def connect(self) -> bool:
        try:
            self.trading_client.get_account()
            return True
        except Exception:
            return False

    async def get_balance(self, currency: str = "USD") -> BalanceInfo:
        # Alpaca uses 'cash' or 'buying_power'
        account = self.trading_client.get_account()
        total = Decimal(str(account.equity))
        available = Decimal(str(account.buying_power))
        return BalanceInfo(total=total, available=available, currency=currency)

    async def get_ticker(self, symbol: str) -> TickerPrice:
        # Alpaca uses symbols like 'AAPL'
        request_params = StockQuotesRequest(symbol_or_symbols=symbol, timeframe=None)
        # Note: data client is synchronous in alpaca-py. In production, wrap in run_in_executor
        quote = self.data_client.get_stock_latest_quote(request_params)[symbol]
        return TickerPrice(
            symbol=symbol,
            bid=Decimal(str(quote.bid_price)),
            ask=Decimal(str(quote.ask_price)),
            last=Decimal(str(quote.ask_price)), # using ask as fallback for price
            timestamp=quote.timestamp.isoformat()
        )

    async def place_order(self, order: TradeOrder) -> TradeResult:
        side = AlpacaSide.BUY if order.side == OrderSide.BUY else AlpacaSide.SELL
        
        if order.order_type == OrderType.MARKET:
            req = MarketOrderRequest(
                symbol=order.symbol,
                qty=float(order.quantity),
                side=side,
                time_in_force=TimeInForce.GTC
            )
        elif order.order_type == OrderType.LIMIT:
            req = LimitOrderRequest(
                symbol=order.symbol,
                qty=float(order.quantity),
                side=side,
                limit_price=float(order.limit_price),
                time_in_force=TimeInForce.GTC
            )
        else:
            raise ValueError(f"Order type {order.order_type} not supported yet in Alpaca connector.")
            
        res = self.trading_client.submit_order(req)
        
        return TradeResult(
            order_id=str(res.id),
            symbol=res.symbol,
            side=OrderSide(res.side.value),
            filled_quantity=Decimal(str(res.filled_qty or 0)),
            filled_price=Decimal(str(res.filled_avg_price or 0)),
            fees=Decimal("0"), # Alpaca is commission free
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
        filter = GetOrdersRequest(status=OrderStatus.OPEN, symbols=[symbol] if symbol else None)
        orders = self.trading_client.get_orders(filter)
        return [dict(o) for o in orders]

    async def get_order_status(self, order_id: str, symbol: str) -> dict:
        order = self.trading_client.get_order_by_id(order_id)
        return dict(order)

    def get_supported_assets(self) -> List[AssetClass]:
        return [AssetClass.STOCK, AssetClass.ETF]

    async def get_minimum_order_size(self, symbol: str) -> Decimal:
        # Alpaca supports fractional shares, min usually 0.000001 or $1
        return Decimal("0.00001")
