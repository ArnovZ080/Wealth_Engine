"""
Funding API Routes — Deposits, Withdrawals, and Transaction History.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from typing import List, Dict, Any

from pydantic import BaseModel
from app.database import get_db
from app.api.deps import get_current_user, get_master_user
from app.models.user import User
from app.services.funding_service import FundingService
from app.services.cashout_service import CashOutService

class WithdrawalRequest(BaseModel):
    zar_amount: Decimal

router = APIRouter(prefix="/funding", tags=["funding"])

@router.get("/deposit-instructions", response_model=Dict[str, Any])
async def get_deposit_instructions(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """
    Get bank details and user's unique deposit reference.
    """
    service = FundingService()
    # Generate reference if missing
    if not current_user.deposit_reference:
        await service.generate_deposit_reference(session, current_user)
    
    return await service.get_deposit_instructions(current_user)

@router.get("/transactions", response_model=List[Dict[str, Any]])
async def get_transactions(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """
    List user's deposit and withdrawal history.
    """
    service = FundingService()
    txs = await service.get_user_transactions(session, current_user.id)
    return [
        {
            "id": tx.id,
            "type": tx.type,
            "zar_amount": float(tx.zar_amount),
            "fx_rate_used": float(tx.fx_rate_used) if tx.fx_rate_used else None,
            "usd_amount": float(tx.usd_amount) if tx.usd_amount else None,
            "status": tx.status,
            "created_at": tx.created_at.isoformat(),
            "completed_at": tx.completed_at.isoformat() if tx.completed_at else None,
            "manual_review": tx.manual_review_flag
        }
        for tx in txs
    ]

@router.post("/deposits/confirm", response_model=Dict[str, Any])
async def confirm_deposit(
    user_id: str,
    zar_amount: Decimal,
    bank_reference: str = None,
    master_user: User = Depends(get_master_user),
    session: AsyncSession = Depends(get_db)
):
    """
    Master manually confirms a deposit and credits the user's internal balance.
    """
    service = FundingService()
    try:
        tx = await service.confirm_deposit(session, user_id, zar_amount, bank_reference)
        return {"success": True, "transaction_id": tx.id, "amount_usdt": float(tx.usd_amount)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/withdraw/preview", response_model=Dict[str, Any])
async def preview_withdrawal(
    data: WithdrawalRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """
    Preview the hierarchical liquidation for a withdrawal request.
    """
    service = CashOutService()
    return await service.preview_withdrawal(session, current_user.id, data.zar_amount)

@router.post("/withdraw/execute", response_model=Dict[str, Any])
async def execute_withdrawal(
    data: WithdrawalRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """
    Initiate a hierarchical liquidation and withdrawal request.
    """
    service = CashOutService()
    try:
        tx = await service.execute_withdrawal(session, current_user.id, data.zar_amount)
        return {"success": True, "transaction_id": tx.id, "status": tx.status}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
