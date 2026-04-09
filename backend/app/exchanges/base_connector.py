"""
Base Exchange Connector — Unified interface for all trading exchanges.

Alpha Hunter and Root Orchestrator call ONLY these methods.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal
from typing import Optional, List

class AssetClass(str, Enum):
    CRYPTO = "crypto"
    STOCK = "stock"
    ETF = "etf"

class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"

class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"

@dataclass
class TradeOrder:
    symbol: str              # e.g., "BTC/USDT" or "AAPL"
    side: OrderSide
    order_type: OrderType
    quantity: Decimal         # units
    limit_price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None

@dataclass
class TradeResult:
    order_id: str
    symbol: str
    side: OrderSide
    filled_quantity: Decimal
    filled_price: Decimal     # average fill price
    fees: Decimal
    fee_currency: str
    timestamp: str
    raw_response: dict

@dataclass
class BalanceInfo:
    total: Decimal
    available: Decimal
    currency: str

@dataclass
class TickerPrice:
    symbol: str
    bid: Decimal
    ask: Decimal
    last: Decimal
    timestamp: str

class BaseExchangeConnector(ABC):
    """
    Unified interface for exchange operations.
    """

    @abstractmethod
    async def connect(self) -> bool:
        """Verify credentials."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Gracefully close the persistent connection."""
        pass

    @abstractmethod
    async def get_balance(self, currency: str = "USDT") -> BalanceInfo:
        pass

    @abstractmethod
    async def get_ticker(self, symbol: str) -> TickerPrice:
        pass

    @abstractmethod
    async def get_ohlcv(self, symbol: str, timeframe: str, limit: int) -> List[List]:
        """Fetch OHLCV data. Returns list of lists [timestamp, open, high, low, close, volume]"""
        pass

    @abstractmethod
    async def place_order(self, order: TradeOrder) -> TradeResult:
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        pass

    @abstractmethod
    async def get_open_orders(self, symbol: Optional[str] = None) -> List:
        pass

    @abstractmethod
    async def get_order_status(self, order_id: str, symbol: str) -> dict:
        pass

    @abstractmethod
    def get_supported_assets(self) -> List[AssetClass]:
        pass

    @abstractmethod
    async def get_minimum_order_size(self, symbol: str) -> Decimal:
        pass

    @staticmethod
    @abstractmethod
    def normalize_symbol(symbol: str) -> str:
        """Translate canonical format (BTC/USDT, AAPL/USD) to exchange-specific format."""
        pass
