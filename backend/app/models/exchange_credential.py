"""
Exchange Credential ORM Model — Encrypted API key storage.

Supports Binance and Alpaca.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    JSON,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class ExchangeCredential(Base):
    """
    Stores encrypted API keys for exchanges.
    Keys must be encrypted/decrypted via CryptoService (Fernet).
    """
    __tablename__ = "exchange_credentials"

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
    
    exchange: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="binance | alpaca",
    )
    
    api_key_encrypted: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )
    
    api_secret_encrypted: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )
    
    additional_config: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )
    
    is_paper_trading: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "exchange", name="uq_user_exchange"),
    )

    # Relationship
    user = relationship("User", back_populates="exchange_credentials")

    def __repr__(self) -> str:
        return f"<ExchangeCredential(user_id={self.user_id}, exchange={self.exchange})>"
