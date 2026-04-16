"""
Seed ORM Model — The atomic trading unit.

Each seed starts at $100 and follows the Bayesian Decision Funnel.
"""

import uuid
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
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum

# Cross-dialect JSON type
_json_type = JSON().with_variant(JSONB(), "postgresql")


class SeedStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    GROUND_ZERO = "ground_zero"
    PRUNED = "pruned"
    CLOSED = "closed"


class Seed(Base):
    """
    Atomic trading unit ($100 base).
    """
    __tablename__ = "seeds"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    
    seed_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        comment="Human-readable ID like 'seed_001_042'",
    )

    tree_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("trees.id"),
        nullable=False,
    )

    current_value: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal("100.00000000"),
        nullable=False,
    )

    initial_value: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal("100.00000000"),
        nullable=False,
    )

    stage: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="Scaling stage (1-4)",
    )

    strategy: Mapped[str] = mapped_column(
        String(30),
        default="momentum",
        nullable=False,
        comment="momentum | exploratory | dumb_baseline | llm",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        nullable=False,
        comment="active | paused | ground_zero | pruned | closed",
    )

    roi_30d: Mapped[Decimal] = mapped_column(
        Numeric(10, 6),
        default=Decimal("0.000000"),
        nullable=False,
    )

    stop_loss_floor: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal("85.00000000"),
        nullable=False,
    )

    strike_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    boost_applied: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    confidence_score: Mapped[float] = mapped_column(
        Numeric(5, 2),
        default=0.0,
        nullable=False,
    )

    last_trade_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    performance_metrics: Mapped[dict] = mapped_column(
        _json_type,
        default=dict,
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

    # Relationships
    tree = relationship("Tree", back_populates="seeds")

    def __repr__(self) -> str:
        return f"<Seed(seed_id={self.seed_id}, value=${self.current_value}, status={self.status})>"
