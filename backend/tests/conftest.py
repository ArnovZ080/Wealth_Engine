"""
Test fixtures for the Fractal Wealth Engine test suite.

Uses SQLite in-memory with aiosqlite for test isolation — no PostgreSQL
dependency required to run tests.

The ORM model uses with_variant() types, so it works natively with SQLite
without any DDL translation needed.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.models.global_state import GlobalState

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def engine():
    """Create a fresh async SQLite engine with the schema from ORM metadata."""
    _engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield _engine

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _engine.dispose()


@pytest_asyncio.fixture
async def session(engine):
    """
    Create an async session with a seeded GlobalState row.

    Uses the ORM model directly — with_variant() columns resolve to
    SQLite-compatible types automatically.
    """
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as _session:
        async with _session.begin():
            now = datetime.now(timezone.utc)
            state = GlobalState(
                id=str(uuid.uuid4()),
                shared_reservoir_balance=Decimal("0"),
                shared_nursery_balance=Decimal("0"),
                vault_tier1_buidl=Decimal("0"),
                vault_tier2_etfs=Decimal("0"),
                vault_tier2_capacity=Decimal("50000"),
                vault_tier3_real_estate=Decimal("0"),
                last_heartbeat=now,
                kill_switch_status="active",
                strike_count=0,
                preflight_passed=False,
                tax_rate=Decimal("0.3000"),
                boost_log=[],
                trees=[],
                legacy_triggered=False,
                legacy_heir_wallet=None,
                legacy_trust_contract=None,
                created_at=now,
                updated_at=now,
            )
            _session.add(state)

        yield _session


@pytest_asyncio.fixture
async def session_factory(engine):
    """Provide the session factory for tests that need multiple sessions."""
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
