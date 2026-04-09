"""
Tree ORM Model — The horizontal scaling unit.

Each tree can manage up to 100 seeds.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Tree(Base):
    """
    Groups up to 100 Seeds. Managed by the Root Orchestrator.
    """
    __tablename__ = "trees"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    
    tree_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        comment="Human-readable ID like 'tree_001'",
    )

    global_state_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("global_state.id"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="paused",
        nullable=False,
        comment="active | paused",
    )

    active_seeds_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    max_seeds: Mapped[int] = mapped_column(
        Integer,
        default=100,
        nullable=False,
    )

    preflight_passed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
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
    seeds = relationship("Seed", back_populates="tree", cascade="all, delete-orphan")
    global_state = relationship("GlobalState", back_populates="tree_records")

    def __repr__(self) -> str:
        return f"<Tree(tree_id={self.tree_id}, status={self.status}, seeds={self.active_seeds_count})>"
