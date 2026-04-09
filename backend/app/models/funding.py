"""
Funding Model — tracking ZAR deposits and withdrawals.

Matches Master Document §12 (Funding Pipeline).
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Boolean,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class FundingTransaction(Base):
    """
    Financial record for a user's ZAR flow.
    """
    __tablename__ = "funding_transactions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
    )

    type: Mapped[str] = mapped_column(String(20), nullable=False) # deposit | withdrawal
    
    amount_zar: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    
    # Real-time exchange rate at confirmation
    exchange_rate: Mapped[Decimal | None] = mapped_column(Numeric(20, 8), nullable=True)
    
    # Credited USDT amount for internal allocation
    exchange_amount: Mapped[Decimal | None] = mapped_column(Numeric(20, 8), nullable=True)
    
    status: Mapped[str] = mapped_column(
        String(20), 
        default="pending", 
        nullable=False,
        comment="pending | confirmed | credited | liquidating | processing | completed | failed"
    )

    reference_code: Mapped[str] = mapped_column(String(20), nullable=False) # e.g. WE-ARN0042
    bank_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    manual_review_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationship
    user = relationship("User", back_populates="funding_transactions")

    def __repr__(self) -> str:
        return f"<FundingTransaction(user={self.user_id}, type={self.type}, state={self.status}, zar={self.amount_zar})>"
