"""
Aggregated API v1 router.

All v1 routes are mounted under /api/v1/ prefix.
"""

from fastapi import APIRouter

from app.api.v1.heartbeat import router as heartbeat_router
from app.api.v1.waterfall import router as waterfall_router
from app.api.v1.seeds import router as seeds_router
from app.api.v1.agents import router as agents_router

router = APIRouter(prefix="/api/v1")

router.include_router(waterfall_router, tags=["waterfall"])
router.include_router(heartbeat_router, tags=["heartbeat"])
router.include_router(seeds_router, tags=["seeds"])
router.include_router(agents_router, tags=["agents"])
