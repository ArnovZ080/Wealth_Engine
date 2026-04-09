"""
User Forest State ORM Model — Per-user financial status and waterfall counters.

Replaces the single-row global_state from Phase 1/2.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Integer,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class UserForestState(Base):
    """
    Financial state for a specific user.
    Handles Reservoir, Nursery, and Tiered Vault balances.
    """
    __tablename__ = "user_forest_state"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )

    # ── Shared Balances (Per-User Forest) ──────────────────────────────
    shared_reservoir_balance: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal("1e-8"),
        nullable=False,
    )
    
    shared_nursery_balance: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal("1e-8"),
        nullable=False,
    )

    # ── Tiered Vault (Per-User Forest) ─────────────────────────────────
    vault_tier1_buidl: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal("1e-8"),
        nullable=False,
    )
    
    vault_tier2_etfs: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal("1e-8"),
        nullable=False,
    )
    
    vault_tier3_realestate: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal("1e-8"),
        nullable=False,
    )

    # ── Monitoring & Safety ────────────────────────────────────────────
    kill_switch_status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        nullable=False,
        comment="active | paused | global_pause",
    )
    
    total_platform_fees_paid: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal("1e-8"),
        nullable=False,
        comment="Cumulative 5% platform fees paid by this member to the Master.",
    )

    # ── Timestamps ──────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationship
    user = relationship("User", back_populates="forest_state")

    def __repr__(self) -> str:
        return f"<UserForestState(user_id={self.user_id}, res={self.shared_reservoir_balance})>"
