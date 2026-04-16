"""
Aggregated API v1 router.

All v1 routes are mounted under /api/v1/ prefix.
"""

from fastapi import APIRouter

from app.api.v1.heartbeat import router as heartbeat_router
from app.api.v1.waterfall import router as waterfall_router
from app.api.v1.seeds import router as seeds_router
from app.api.v1.agents import router as agents_router
from app.auth.routes import router as auth_router
from app.admin.routes import router as admin_router
from app.exchanges.routes import router as exchanges_router
from app.api.v1.orchestrator import router as orchestrator_router
from app.api.v1.monitor import router as monitor_router
from app.api.v1.scheduler import router as scheduler_router
from app.api.v1.funding import router as funding_router
from app.api.v1.research import router as research_router
from app.api.v1.health import router as health_router

router = APIRouter(prefix="/api/v1")

# Core Engine
router.include_router(waterfall_router, tags=["waterfall"])
router.include_router(heartbeat_router, tags=["heartbeat"])
router.include_router(seeds_router, tags=["seeds"])
router.include_router(agents_router, tags=["agents"])
router.include_router(orchestrator_router, tags=["orchestrator"])
router.include_router(monitor_router, prefix="/monitor", tags=["monitor"])
router.include_router(scheduler_router, prefix="/scheduler", tags=["scheduler"])
router.include_router(funding_router)
router.include_router(research_router)
router.include_router(health_router)

# Infrastructure & Multi-Tenancy
router.include_router(auth_router)
router.include_router(admin_router)
router.include_router(exchanges_router)
