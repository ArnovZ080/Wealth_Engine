"""
GlobalState ORM model — The Unified Root.

Maps directly to the Global_State schema from the Master Document §9.2.
All monetary fields use NUMERIC(20,8) to preserve Decimal precision.
JSONB columns store the hierarchical Trees/Seeds structure and Boost logs.

Design Decisions:
  - Single-row table pattern: The entire forest shares one global state row.
    This simplifies atomic waterfall transactions (single SELECT FOR UPDATE).
  - JSONB for Trees: The tree/seed hierarchy is deeply nested and varies per
    forest. JSONB gives us schema flexibility while PostgreSQL's GIN indexes
    allow efficient queries into the structure when needed.
  - Separate numeric columns for vault tiers: Even though these could live in
    JSONB, they are individual columns because the waterfall function must
    atomically increment them with row-level locking. JSONB partial updates
    under concurrent writes are error-prone.
  - Cross-dialect types: UUID and JSONB use with_variant() so the ORM works
    with both PostgreSQL (production) and SQLite (tests) without code changes.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, _uuid_type, _jsonb_type




class GlobalState(Base):
    """
    The Unified Root — single-row global state for the entire Fractal Wealth Engine.

    Corresponds to Master Document §9.2: Database Schema (Unified Root).
    """

    __tablename__ = "global_state"

    # ── Primary Key ─────────────────────────────────────────────────────
    id: Mapped[str] = mapped_column(
        _uuid_type,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # ── Shared Balances ─────────────────────────────────────────────────
    # Reservoir = Tier 1 (BUIDL / T-Bills) — instant-access spending wallet
    shared_reservoir_balance: Mapped[float] = mapped_column(
        Numeric(20, 8),
        nullable=False,
        default=0,
        server_default=text("0"),
    )

    # Nursery = USDC stablecoin pool — funds new $100 seeds
    shared_nursery_balance: Mapped[float] = mapped_column(
        Numeric(20, 8),
        nullable=False,
        default=0,
        server_default=text("0"),
    )

    # ── Tiered Vault ────────────────────────────────────────────────────
    # Tier 1: BlackRock BUIDL / T-Bills (also serves as Reservoir backing)
    vault_tier1_buidl: Mapped[float] = mapped_column(
        Numeric(20, 8),
        nullable=False,
        default=0,
        server_default=text("0"),
    )

    # Tier 2: Low-cost Index ETFs (VOO / QQQ) — fills before Tier 3
    vault_tier2_etfs: Mapped[float] = mapped_column(
        Numeric(20, 8),
        nullable=False,
        default=0,
        server_default=text("0"),
    )

    # Tier 2 saturation cap — configurable, default $50,000
    vault_tier2_capacity: Mapped[float] = mapped_column(
        Numeric(20, 8),
        nullable=False,
        default=50000,
        server_default=text("50000"),
    )

    # Tier 3: Tokenized Real Estate (RealT / Centrifuge) — overflow from Tier 2
    vault_tier3_real_estate: Mapped[float] = mapped_column(
        Numeric(20, 8),
        nullable=False,
        default=0,
        server_default=text("0"),
    )

    # ── Heartbeat & Legacy ──────────────────────────────────────────────
    last_heartbeat: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    legacy_heir_wallet: Mapped[str | None] = mapped_column(
        String(256),
        nullable=True,
        default=None,
    )

    legacy_trust_contract: Mapped[str | None] = mapped_column(
        String(256),
        nullable=True,
        default=None,
    )

    legacy_triggered: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )

    # ── Kill Switch & Monitoring ────────────────────────────────────────
    kill_switch_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
    )

    strike_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )

    preflight_passed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )

    # ── Tax Rate ────────────────────────────────────────────────────────
    tax_rate: Mapped[float] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=0.30,
    )

    # ── JSONB Fields ────────────────────────────────────────────────────
    # Boost log: array of {type: "expansion|acceleration|fortress", amount: Decimal, timestamp: ISO}
    boost_log: Mapped[list | None] = mapped_column(
        _jsonb_type,
        nullable=False,
        default=list,
    )

    total_active_seeds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # ── Relationships ───────────────────────────────────────────────────
    tree_records = relationship("Tree", back_populates="global_state", cascade="all, delete-orphan")

    # ── Timestamps ──────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # ── Indexes ─────────────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_global_state_last_heartbeat", "last_heartbeat"),
        Index("ix_global_state_kill_switch", "kill_switch_status"),
    )

    def __repr__(self) -> str:
        return (
            f"<GlobalState("
            f"reservoir={self.shared_reservoir_balance}, "
            f"nursery={self.shared_nursery_balance}, "
            f"vault_t2={self.vault_tier2_etfs}, "
            f"vault_t3={self.vault_tier3_real_estate}, "
            f"heartbeat={self.last_heartbeat}, "
            f"kill_switch={self.kill_switch_status}"
            f")>"
        )
