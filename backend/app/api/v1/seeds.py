"""
Seeds API — Tree and Seed management.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.tree import Tree
from app.models.seed import Seed, SeedStatus
from sqlalchemy import select

router = APIRouter()

@router.get("/trees")
async def list_trees(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    stmt = select(Tree).where(Tree.user_id == current_user.id)
    result = await session.execute(stmt)
    trees = result.scalars().all()
    return [
        {
            "id": str(t.id),
            "name": t.tree_id,
            "is_active": t.status == "active",
            "user_id": str(t.user_id),
            "seed_count": t.active_seeds_count,
            "performance_30d": 0.0,
            "status": t.status
        }
        for t in trees
    ]

@router.get("/trees/{tree_id}")
async def get_tree(
    tree_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    stmt = select(Tree).where(Tree.id == tree_id, Tree.user_id == current_user.id)
    result = await session.execute(stmt)
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tree not found")
    return {
        "id": str(t.id),
        "name": t.tree_id,
        "is_active": t.status == "active",
        "user_id": str(t.user_id),
        "seed_count": t.active_seeds_count,
        "performance_30d": 0.0,
        "status": t.status
    }

@router.get("/trees/{tree_id}/seeds")
async def list_tree_seeds(
    tree_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    tree_stmt = select(Tree).where(Tree.id == tree_id, Tree.user_id == current_user.id)
    tree_res = await session.execute(tree_stmt)
    if not tree_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Tree not found")
    stmt = select(Seed).where(Seed.tree_id == tree_id)
    result = await session.execute(stmt)
    seeds = result.scalars().all()
    return [
        {
            "id": str(s.id),
            "tree_id": str(s.tree_id),
            "strategy_type": s.strategy,
            "current_value": float(s.current_value),
            "strike_count": s.strike_count,
            "is_active": s.status == SeedStatus.ACTIVE,
            "ground_zero_triggered": s.status == SeedStatus.GROUND_ZERO,
            "created_at": s.created_at.isoformat(),
            "status": s.status
        }
        for s in seeds
    ]

@router.post("/trees/{tree_id}/authorize")
async def authorize_tree_endpoint(
    tree_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    return {"message": f"Tree {tree_id} authorized."}

@router.post("/trees/{tree_id}/plant")
async def plant_seed_endpoint(
    tree_id: str,
    seed_id: str,
    strategy: str = "momentum",
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    raise HTTPException(status_code=400, detail="Use the automated nursery planting flow.")

@router.get("/seeds/{seed_id}")
async def get_seed_endpoint(
    seed_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    stmt = select(Seed).where(Seed.id == seed_id)
    result = await session.execute(stmt)
    seed = result.scalar_one_or_none()
    if not seed:
        raise HTTPException(status_code=404, detail="Seed not found.")
    return seed
