"""
Seed Manager Service — Seed lifecycle and Ground Zero protocol.

Implements Master Document §6 and Phase 2 directives.
"""

import logging
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.seed import Seed
from app.models.tree import Tree
from app.models.global_state import GlobalState
from app.services.state_manager import get_global_state

logger = logging.getLogger(__name__)

async def get_seed(session: AsyncSession, seed_id: str) -> Seed | None:
    """Fetch a seed by its human-readable ID."""
    stmt = select(Seed).where(Seed.seed_id == seed_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def create_seed_record(
    session: AsyncSession,
    tree_id: str,
    seed_id: str,
    strategy: str = "momentum",
    initial_value: Decimal = Decimal("100.0")
) -> Seed:
    """
    Creates a new seed record (DB only).
    Note: Balances are not deducted here; handled by the Root Orchestrator.
    """
    seed = Seed(
        seed_id=seed_id,
        tree_id=tree_id,
        strategy=strategy,
        initial_value=initial_value,
        current_value=initial_value,
        status="active"
    )
    session.add(seed)
    
    # Update tree count
    await session.execute(
        update(Tree)
        .where(Tree.id == tree_id)
        .values(active_seeds_count=Tree.active_seeds_count + 1)
    )
    
    return seed

async def check_ground_zero(session: AsyncSession, seed: Seed) -> bool:
    """
    Checks if a seed has hit the $85 Ground Zero floor.
    Returns True if triggered.
    """
    if seed.current_value <= seed.stop_loss_floor and seed.status == "active":
        logger.warning("Ground Zero triggered for seed %s: value $%s", seed.seed_id, seed.current_value)
        return True
    return False

async def trigger_ground_zero(session: AsyncSession, seed: Seed):
    """
    Executes the Ground Zero protocol:
    1. Pauses the seed.
    2. Increments per-seed strikes.
    3. Increments global global_state strikes.
    """
    seed.status = "ground_zero"
    seed.strike_count += 1
    
    state = await get_global_state(session, for_update=True)
    state.strike_count += 1
    
    if state.strike_count >= 3:
        state.kill_switch_status = "global_pause"
        logger.critical("FLEET-WIDE KILL SWITCH: 3 strikes reached.")
    
    logger.info("Seed %s moved to ground_zero. Global strikes: %s", seed.seed_id, state.strike_count)

async def request_seed_reset(session: AsyncSession, seed: Seed):
    """
    Requests a reset from $85 -> $100.
    Root Orchestrator will authorize the Vault/Nursery movement.
    """
    # Simply flags for reset; manual or orchestrated later
    seed.status = "paused"
    logger.info("Seed %s flagged for reset authorization.", seed.seed_id)
