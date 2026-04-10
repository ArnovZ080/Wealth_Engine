"""
Auth Routes — Multi-tenant registration and login.

Implements invite-only registration and JWT loops.
"""

from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

from app.database import get_session
from app.models.user import User, UserRole, InviteCode
from app.models.forest import UserForestState
from app.auth.jwt_handler import create_access_token, create_refresh_token, decode_token
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class RegisterSchema(BaseModel):
    email: EmailStr
    password: str
    display_name: str
    invite_code: str

class LoginSchema(BaseModel):
    email: str
    password: str

class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

@router.post("/register", response_model=TokenSchema)
async def register(data: RegisterSchema, session: AsyncSession = Depends(get_session)):
    """Registration required a valid invite code."""
    # 1. Check if user exists
    stmt = select(User).where(User.email == data.email)
    res = await session.execute(stmt)
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2. Verify and claim invite code
    invite_stmt = select(InviteCode).where(InviteCode.code == data.invite_code, InviteCode.claimed_by == None)
    res = await session.execute(invite_stmt)
    invite = res.scalar_one_or_none()
    if not invite:
        raise HTTPException(status_code=400, detail="Invalid or already used invite code")

    # 3. Create user
    # Check if first user and if it matches MASTER_EMAIL (handled by migration or admin logic)
    # For now, default to member role
    new_user = User(
        email=data.email,
        display_name=data.display_name,
        hashed_password=pwd_context.hash(data.password),
        role=UserRole.MEMBER,
        invited_by=invite.created_by
    )
    session.add(new_user)
    await session.flush() # Get user.id

    # 4. Claim invite
    invite.claimed_by = new_user.id
    invite.claimed_at = datetime.now(timezone.utc)

    # 5. Create Forest State
    forest = UserForestState(user_id=new_user.id)
    session.add(forest)

    await session.commit()
    
    access = create_access_token({"sub": new_user.email})
    refresh = create_refresh_token({"sub": new_user.email})
    return {"access_token": access, "refresh_token": refresh}

@router.post("/login", response_model=TokenSchema)
async def login(data: LoginSchema, session: AsyncSession = Depends(get_session)):
    stmt = select(User).where(User.email == data.email)
    res = await session.execute(stmt)
    user = res.scalar_one_or_none()
    
    if not user or not pwd_context.verify(data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    access = create_access_token({"sub": user.email})
    refresh = create_refresh_token({"sub": user.email})
    return {"access_token": access, "refresh_token": refresh}

@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "role": user.role,
        "platform_fee_rate": float(user.platform_fee_rate)
    }

@router.post("/heartbeat")
async def user_heartbeat(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    user.last_heartbeat = datetime.now(timezone.utc)
    await session.commit()
    return {"status": "ok", "last_heartbeat": user.last_heartbeat}

class TelegramLinkSchema(BaseModel):
    chat_id: str

@router.post("/telegram")
async def link_telegram(data: TelegramLinkSchema, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """
    Link a user to their Telegram chat ID for notifications.
    """
    user.telegram_chat_id = data.chat_id
    await session.commit()
    
    # Send a confirmation if possible
    from app.services.telegram_service import TelegramService
    telegram = TelegramService()
    await telegram.send_message(data.chat_id, f"✅ <b>Wealth Engine Linked</b>\nHello {user.display_name}! You will now receive trade alerts here.")
    
    return {"status": "linked", "chat_id": data.chat_id}
