"""
Forest State Manager — per-user financial status management.

Replaces the single-row Global State Manager from Phase 1/2.
All operations use user_id scoping and SELECT FOR UPDATE row locking.
"""

import logging
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.forest import UserForestState
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)


# ── Backward-compat: Legacy GlobalState query ───────────────────────────
# heartbeat.py, tree_manager.py, seed_manager.py still reference the
# single-row GlobalState table.  These services use fields that ONLY
# exist on GlobalState (legacy_triggered, strike_count, total_active_seeds,
# legacy_heir_wallet, etc.) and do NOT exist on UserForestState.
# This wrapper keeps them working without a schema migration.
# It reads from the actual GlobalState table — no user_id needed.

async def get_global_state(
    session: AsyncSession,
    *,
    for_update: bool = False,
):
    """
    Fetch the single-row legacy GlobalState.

    This is NOT user-scoped — it reads the one-row ``global_state`` table
    that predates the Phase 3A multi-tenant refactor.  Services that need
    per-user state should use ``get_user_forest_state()`` instead.
    """
    from app.models.global_state import GlobalState

    stmt = select(GlobalState)
    if for_update:
        stmt = stmt.with_for_update()

    result = await session.execute(stmt)
    state = result.scalar_one_or_none()

    if state is None:
        # Auto-create a default row so the app doesn't crash on first boot
        state = GlobalState()
        session.add(state)
        await session.flush()

    return state


# ── Per-User Forest State ───────────────────────────────────────────────

async def get_user_forest_state(
    session: AsyncSession,
    user_id: str,
    *,
    for_update: bool = False,
) -> UserForestState:
    """
    Retrieve the forest state for a specific user.
    """
    stmt = select(UserForestState).where(UserForestState.user_id == user_id)
    if for_update:
        stmt = stmt.with_for_update()

    result = await session.execute(stmt)
    state = result.scalar_one_or_none()

    if state is None:
        raise ValueError(f"Forest state not found for user {user_id}.")

    return state

async def get_master_forest_state(
    session: AsyncSession,
    *,
    for_update: bool = False,
) -> UserForestState:
    """
    Utility to fetch the Master user's forest state (e.g., for platform fees).
    """
    stmt = select(UserForestState).join(User).where(User.role == UserRole.MASTER)
    if for_update:
        stmt = stmt.with_for_update()
        
    result = await session.execute(stmt)
    state = result.scalar_one_or_none()
    
    if state is None:
        raise ValueError("Master forest state not found. Has the Master account been seeded?")
        
    return state

async def get_vault_tier2_remaining_capacity(
    session: AsyncSession,
    state: UserForestState,
) -> Decimal:
    """
    Calculate remaining Tier 2 ETF capacity.
    """
    from app.config import get_settings
    settings = get_settings()
    
    current = Decimal(str(state.vault_tier2_etfs))
    capacity = settings.default_tier2_capacity
    remaining = capacity - current

    return max(Decimal("0"), remaining)

async def update_balances(
    session: AsyncSession,
    state: UserForestState,
    *,
    reservoir_delta: Decimal = Decimal("0"),
    nursery_delta: Decimal = Decimal("0"),
    vault_tier2_delta: Decimal = Decimal("0"),
    vault_tier3_delta: Decimal = Decimal("0"),
) -> UserForestState:
    """
    Atomically update balance fields by delta amounts for a specific user.
    """
    state.shared_reservoir_balance = Decimal(str(state.shared_reservoir_balance)) + reservoir_delta
    state.shared_nursery_balance = Decimal(str(state.shared_nursery_balance)) + nursery_delta
    state.vault_tier2_etfs = Decimal(str(state.vault_tier2_etfs)) + vault_tier2_delta
    state.vault_tier3_realestate = Decimal(str(state.vault_tier3_realestate)) + vault_tier3_delta

    logger.debug(
        "User %s Balances updated — Δres=%s, Δnur=%s, Δt2=%s, Δt3=%s",
        state.user_id,
        reservoir_delta,
        nursery_delta,
        vault_tier2_delta,
        vault_tier3_delta,
    )

    return state

