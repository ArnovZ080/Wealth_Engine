"""
Admin Routes — Master-only forest management and invitations.
"""

import secrets
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from app.database import get_session
from app.models.user import User, InviteCode, UserRole
from app.models.forest import UserForestState
from app.auth.dependencies import require_master

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/invites")
async def create_invite(
    master: User = Depends(require_master),
    session: AsyncSession = Depends(get_session)
):
    """Generates an 8-char alphanumeric invite code."""
    code = secrets.token_hex(4).upper() # 8 chars
    new_invite = InviteCode(
        code=code,
        created_by=master.id
    )
    session.add(new_invite)
    await session.commit()
    return {"code": code}

@router.get("/invites")
async def list_invites(
    master: User = Depends(require_master),
    session: AsyncSession = Depends(get_session)
):
    stmt = select(InviteCode).order_by(InviteCode.created_at.desc())
    res = await session.execute(stmt)
    return res.scalars().all()

@router.get("/users")
async def list_users(
    master: User = Depends(require_master),
    session: AsyncSession = Depends(get_session)
):
    """List all users with forest summary."""
    stmt = (
        select(User, UserForestState)
        .join(UserForestState, isouter=True)
        .order_by(User.created_at.desc())
    )
    res = await session.execute(stmt)
    results = []
    for user, forest in res.all():
        results.append({
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "role": user.role,
            "is_active": user.is_active,
            "forest": {
                "reservoir": float(forest.shared_reservoir_balance) if forest else 0,
                "nursery": float(forest.shared_nursery_balance) if forest else 0,
                "total_fees_paid": float(forest.total_platform_fees_paid) if forest else 0
            } if forest else None
        })
    return results

@router.patch("/users/{user_id}/fee-rate")
async def update_fee_rate(
    user_id: str,
    fee_rate: float,
    master: User = Depends(require_master),
    session: AsyncSession = Depends(get_session)
):
    """Master adjusts a member's platform fee."""
    user_stmt = select(User).where(User.id == user_id)
    res = await session.execute(user_stmt)
    user = res.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.platform_fee_rate = Decimal(str(fee_rate))
    await session.commit()
    return {"status": "ok", "new_fee_rate": float(user.platform_fee_rate)}

@router.get("/platform-revenue")
async def get_platform_revenue(
    master: User = Depends(require_master),
    session: AsyncSession = Depends(get_session)
):
    """Total revenue collected from platform fees."""
    stmt = select(func.sum(UserForestState.total_platform_fees_paid))
    res = await session.execute(stmt)
    total = res.scalar() or 0
    return {"total_revenue": float(total)}
