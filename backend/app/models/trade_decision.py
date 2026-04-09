"""
TradeDecision ORM Model — The adversarial loop output.

Stores the genetic 'DNA' of every trade for the Researcher Agent.
"""

import uuid
from typing import Optional, List
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    JSON,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

# Cross-dialect JSON type
_json_type = JSON().with_variant(JSONB(), "postgresql")

class TradeDecision(Base):
    """
    Final decision from a Hunter-Shadow adversarial loop.
    """
    __tablename__ = "trade_decisions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    
    seed_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("seeds.id"),
        nullable=False,
    )

    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False) # long | short
    
    entry_price: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    target_exit: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    stop_loss: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    position_size: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)

    confidence_score: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Adversarial metadata
    hunter_rationale: Mapped[str] = mapped_column(Text, nullable=False)
    shadow_verdict: Mapped[str] = mapped_column(String(20), nullable=False) # APPROVE | VETO | REFINE
    shadow_flaws: Mapped[dict] = mapped_column(_json_type, default=list, nullable=False)
    
    refinement_rounds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    execution_authorized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    executed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    dumb_mode_agreed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Position Watcher fields
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)
    exit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8), nullable=True)
    exit_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    exit_reason: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    highest_price_since_entry: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8), nullable=True)
    realized_pnl: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8), nullable=True)
    trailing_stop_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Full trade DNA
    trade_memo: Mapped[dict] = mapped_column(_json_type, nullable=False)
    adversarial_log: Mapped[dict] = mapped_column(_json_type, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<TradeDecision(ticker={self.ticker}, auth={self.execution_authorized}, verdict={self.shadow_verdict})>"
