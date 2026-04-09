"""
Seeds API — Tree and Seed management.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.services.tree_manager import plant_seed, authorize_tree
from app.services.seed_manager import get_seed
from app.models.tree import Tree
from app.models.seed import Seed
from sqlalchemy import select

router = APIRouter()

@router.get("/trees")
async def list_trees(session: AsyncSession = Depends(get_session)):
    stmt = select(Tree)
    result = await session.execute(stmt)
    return result.scalars().all()

@router.post("/trees/{tree_id}/authorize")
async def authorize_tree_endpoint(tree_id: str, session: AsyncSession = Depends(get_session)):
    await authorize_tree(session, tree_id)
    await session.commit()
    return {"message": f"Tree {tree_id} authorized."}

@router.post("/trees/{tree_id}/plant")
async def plant_seed_endpoint(
    tree_id: str, 
    seed_id: str, 
    strategy: str = "momentum", 
    session: AsyncSession = Depends(get_session)
):
    seed = await plant_seed(session, tree_id, seed_id, strategy)
    if not seed:
        raise HTTPException(status_code=400, detail="Failed to plant seed. Check capacity or Nursery balance.")
    await session.commit()
    return seed

@router.get("/seeds/{seed_id}")
async def get_seed_endpoint(seed_id: str, session: AsyncSession = Depends(get_session)):
    seed = await get_seed(session, seed_id)
    if not seed:
        raise HTTPException(status_code=404, detail="Seed not found.")
    return seed
