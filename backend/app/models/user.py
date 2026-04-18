"""
User and InviteCode ORM Models — Multi-tenancy and Invitational System.

Master: 0% Platform Fee, controls invites.
Member: 5% Platform Fee, required invite code for registration.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Enum,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base, _uuid_type
import enum

class UserRole(str, enum.Enum):
    MASTER = "master"
    MEMBER = "member"

class User(Base):
    """
    Forest Owner. Every user manages their own isolated Wealth Engine ecosystem.
    """
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        _uuid_type,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )
    
    display_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    role: Mapped[UserRole] = mapped_column(
        String(20),
        default=UserRole.MEMBER,
        nullable=False,
    )
    
    invited_by: Mapped[str | None] = mapped_column(
        _uuid_type,
        ForeignKey("users.id"),
        nullable=True,
    )
    
    platform_fee_rate: Mapped[float] = mapped_column(
        Numeric(5, 4),
        default=0.0500,
        nullable=False,
        comment="Master can adjust this per-user. 0.05 is 5%.",
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=text("true"),
        nullable=False,
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    
    last_heartbeat: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # ── Funding & Banking (Phase 4) ───────────────────────────────────
    deposit_reference: Mapped[str | None] = mapped_column(
        String(20),
        unique=True,
        nullable=True,
        comment="Unique EFT reference e.g., WE-ARN0042",
    )
    
    bank_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    bank_account_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    bank_branch_code: Mapped[str | None] = mapped_column(String(20), nullable=True)

    telegram_chat_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    telegram_alerts_enabled: Mapped[bool] = mapped_column(Boolean, server_default=text("true"), default=True)
    ground_zero_alerts_enabled: Mapped[bool] = mapped_column(Boolean, server_default=text("true"), default=True)
    trade_signals_enabled: Mapped[bool] = mapped_column(Boolean, server_default=text("true"), default=True)

    # Relationships
    forest_state = relationship("UserForestState", back_populates="user", uselist=False, cascade="all, delete-orphan")
    exchange_credentials = relationship("ExchangeCredential", back_populates="user", cascade="all, delete-orphan")
    trees = relationship("Tree", back_populates="user", cascade="all, delete-orphan")
    funding_transactions = relationship("FundingTransaction", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(email={self.email}, role={self.role})>"

class InviteCode(Base):
    """
    One-time use alphanumeric codes for private registration.
    """
    __tablename__ = "invite_codes"

    id: Mapped[str] = mapped_column(
        _uuid_type,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    
    code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
    )
    
    created_by: Mapped[str] = mapped_column(
        _uuid_type,
        ForeignKey("users.id"),
        nullable=False,
    )
    
    claimed_by: Mapped[str | None] = mapped_column(
        _uuid_type,
        ForeignKey("users.id"),
        nullable=True,
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    
    claimed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<InviteCode(code={self.code}, claimed={self.claimed_by is not None})>"
