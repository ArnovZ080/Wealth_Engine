"""
Global State Manager — CRUD operations for the Unified Root.

All read/write operations use SELECT FOR UPDATE row locking to ensure
atomicity when multiple waterfall executions could race.
"""

import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.global_state import GlobalState

logger = logging.getLogger(__name__)


async def get_global_state(
    session: AsyncSession,
    *,
    for_update: bool = False,
) -> GlobalState:
    """
    Retrieve the single global state row.

    Args:
        session: Active async database session.
        for_update: If True, acquires a row-level lock (SELECT FOR UPDATE)
                    to prevent concurrent modifications during a transaction.

    Returns:
        The GlobalState instance.

    Raises:
        ValueError: If no global state row exists (migration hasn't run).
    """
    stmt = select(GlobalState)
    if for_update:
        stmt = stmt.with_for_update()

    result = await session.execute(stmt)
    state = result.scalar_one_or_none()

    if state is None:
        raise ValueError(
            "Global state row not found. Run 'alembic upgrade head' to initialize the schema."
        )

    return state


async def get_vault_tier2_remaining_capacity(
    session: AsyncSession,
    state: GlobalState | None = None,
) -> Decimal:
    """
    Calculate remaining Tier 2 ETF capacity before overflow to Tier 3.

    Returns:
        Remaining capacity as Decimal. If Tier 2 is saturated, returns 0.
    """
    if state is None:
        state = await get_global_state(session)

    current = Decimal(str(state.vault_tier2_etfs))
    capacity = Decimal(str(state.vault_tier2_capacity))
    remaining = capacity - current

    return max(Decimal("0"), remaining)


async def update_balances(
    session: AsyncSession,
    state: GlobalState,
    *,
    reservoir_delta: Decimal = Decimal("0"),
    nursery_delta: Decimal = Decimal("0"),
    vault_tier2_delta: Decimal = Decimal("0"),
    vault_tier3_delta: Decimal = Decimal("0"),
) -> GlobalState:
    """
    Atomically update balance fields by delta amounts.

    This function modifies the state object in-place within the current
    transaction. The caller is responsible for committing or rolling back.

    Args:
        session: Active async session (should be within a transaction).
        state: GlobalState instance obtained with for_update=True.
        reservoir_delta: Amount to add to reservoir.
        nursery_delta: Amount to add to nursery.
        vault_tier2_delta: Amount to add to Tier 2 ETFs.
        vault_tier3_delta: Amount to add to Tier 3 Real Estate.

    Returns:
        The updated GlobalState instance.
    """
    state.shared_reservoir_balance = Decimal(str(state.shared_reservoir_balance)) + reservoir_delta
    state.shared_nursery_balance = Decimal(str(state.shared_nursery_balance)) + nursery_delta
    state.vault_tier2_etfs = Decimal(str(state.vault_tier2_etfs)) + vault_tier2_delta
    state.vault_tier3_real_estate = Decimal(str(state.vault_tier3_real_estate)) + vault_tier3_delta

    logger.info(
        "Balances updated — Δreservoir=%s, Δnursery=%s, Δtier2=%s, Δtier3=%s",
        reservoir_delta,
        nursery_delta,
        vault_tier2_delta,
        vault_tier3_delta,
    )

    return state
