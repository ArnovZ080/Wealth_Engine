"""
Tree Manager Service — Tree and Seed fleet operations.

Handles seed planting authorization and 100-seed cap logic.
"""

import logging
from decimal import Decimal
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tree import Tree
from app.models.seed import Seed
from app.models.global_state import GlobalState
from app.services.state_manager import get_global_state

logger = logging.getLogger(__name__)

async def authorize_tree(session: AsyncSession, tree_id: str):
    """Activates a paused tree."""
    stmt = update(Tree).where(Tree.tree_id == tree_id).values(status="active")
    await session.execute(stmt)
    logger.info("Tree %s authorized and activated.", tree_id)

async def plant_seed(
    session: AsyncSession,
    tree_id_str: str,
    new_seed_id: str,
    strategy: str = "momentum"
) -> Seed | None:
    """
    Plants a new seed in a tree.
    
    Logic:
    1. Check if tree is active and has capacity (< 100 seeds).
    2. Check if Nursery has >= $100.
    3. Deduct $100 from Nursery.
    4. Create Seed record.
    5. Update total_active_seeds in GlobalState.
    """
    # 1. Check tree capacity and status
    stmt = select(Tree).where(Tree.tree_id == tree_id_str)
    result = await session.execute(stmt)
    tree = result.scalar_one_or_none()
    
    if not tree:
        logger.error("Tree %s not found.", tree_id_str)
        return None
    
    if tree.status != "active":
        logger.warning("Cannot plant in tree %s: status is %s", tree_id_str, tree.status)
        return None
    
    if tree.active_seeds_count >= tree.max_seeds:
        logger.warning("Tree %s is full (%s/%s seeds). Triggering Genetic Pruning logic soon.", 
                      tree_id_str, tree.active_seeds_count, tree.max_seeds)
        # TODO: Implement Genetic Pruning trigger here
        return None

    # 2. Check Global State / Nursery
    state = await get_global_state(session, for_update=True)
    if state.shared_nursery_balance < Decimal("100.0"):
        logger.warning("Nursery balance too low to plant seed ($%s < $100)", state.shared_nursery_balance)
        return None

    # 3. Deduct from Nursery
    state.shared_nursery_balance -= Decimal("100.0")
    state.total_active_seeds += 1

    # 4. Create Seed
    seed = Seed(
        seed_id=new_seed_id,
        tree_id=tree.id,
        strategy=strategy,
        initial_value=Decimal("100.0"),
        current_value=Decimal("100.0"),
        status="active"
    )
    session.add(seed)
    
    # 5. Increment tree count
    tree.active_seeds_count += 1
    
    logger.info("Planted seed %s in tree %s. Nursery balance: $%s", 
                new_seed_id, tree_id_str, state.shared_nursery_balance)
    return seed

async def get_weakest_seed(session: AsyncSession, tree_id: str) -> Seed | None:
    """Finds the lowest performing 30D ROI seed in a tree for Genetic Pruning."""
    stmt = (
        select(Seed)
        .where(Seed.tree_id == tree_id, Seed.status == "active")
        .order_by(Seed.roi_30d.asc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
