"""
Exchange Routes — Credential management and unified trading interface.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_session
from app.models.user import User
from app.models.exchange_credential import ExchangeCredential
from app.auth.dependencies import get_current_user
from app.services.crypto_service import encrypt
from app.exchanges.connector_factory import ConnectorFactory
from app.exchanges.base_connector import TradeOrder, OrderSide, OrderType
from decimal import Decimal

router = APIRouter(prefix="/exchanges", tags=["exchanges"])

class CredentialSchema(BaseModel):
    exchange: str
    api_key: str
    api_secret: str
    is_paper_trading: bool = True

class PaperOrderSchema(BaseModel):
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    limit_price: Optional[float] = None

@router.post("/credentials")
async def store_credentials(
    data: CredentialSchema,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Encrypted storage of API keys."""
    # Check if exists
    stmt = select(ExchangeCredential).where(
        ExchangeCredential.user_id == user.id,
        ExchangeCredential.exchange == data.exchange.lower()
    )
    res = await session.execute(stmt)
    cred = res.scalar_one_or_none()
    
    if cred:
        cred.api_key_encrypted = encrypt(data.api_key)
        cred.api_secret_encrypted = encrypt(data.api_secret)
        cred.is_paper_trading = data.is_paper_trading
        cred.is_active = True
    else:
        cred = ExchangeCredential(
            user_id=user.id,
            exchange=data.exchange.lower(),
            api_key_encrypted=encrypt(data.api_key),
            api_secret_encrypted=encrypt(data.api_secret),
            is_paper_trading=data.is_paper_trading
        )
        session.add(cred)
    
    await session.commit()
    return {"status": "ok", "message": f"Credentials stored for {data.exchange}"}

@router.get("/credentials")
async def list_credentials(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    stmt = select(ExchangeCredential).where(ExchangeCredential.user_id == user.id)
    res = await session.execute(stmt)
    creds = res.scalars().all()
    return [{
        "exchange": c.exchange,
        "is_paper_trading": c.is_paper_trading,
        "is_active": c.is_active,
        "created_at": c.created_at
    } for c in creds]

@router.delete("/credentials/{exchange}")
async def delete_credential(exchange: str, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    stmt = delete(ExchangeCredential).where(
        ExchangeCredential.user_id == user.id,
        ExchangeCredential.exchange == exchange.lower()
    )
    await session.execute(stmt)
    await session.commit()
    return {"status": "ok"}

@router.post("/credentials/{exchange}/test")
async def test_credentials(exchange: str, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    try:
        connector = await ConnectorFactory.get_connector(user.id, exchange.lower(), session)
        balance = await connector.get_balance()
        return {"status": "success", "balance": float(balance.available), "currency": balance.currency}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@router.get("/{exchange}/balance")
async def get_balance(exchange: str, currency: str = "USDT", user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    connector = await ConnectorFactory.get_connector(user.id, exchange.lower(), session)
    balance = await connector.get_balance(currency)
    return balance

@router.get("/{exchange}/ticker/{symbol}")
async def get_ticker(exchange: str, symbol: str, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    # symbols for binance usually 'BTC/USDT', for alpaca 'AAPL'
    connector = await ConnectorFactory.get_connector(user.id, exchange.lower(), session)
    return await connector.get_ticker(symbol)

@router.post("/{exchange}/paper-order")
async def place_paper_order(
    exchange: str,
    data: PaperOrderSchema,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Safety-first paper order placement."""
    stmt = select(ExchangeCredential).where(
        ExchangeCredential.user_id == user.id,
        ExchangeCredential.exchange == exchange.lower()
    )
    res = await session.execute(stmt)
    cred = res.scalar_one_or_none()
    
    if not cred or not cred.is_paper_trading:
        raise HTTPException(status_code=400, detail="Paper order only allowed on paper-enabled credentials.")
        
    connector = await ConnectorFactory.get_connector(user.id, exchange.lower(), session)
    order = TradeOrder(
        symbol=data.symbol,
        side=data.side,
        order_type=data.order_type,
        quantity=Decimal(str(data.quantity)),
        limit_price=Decimal(str(data.limit_price)) if data.limit_price else None
    )
    return await connector.place_order(order)
