"""
Recursive Fractal Wealth Engine — FastAPI Application Entry Point.

Phase 1: Shared Root & Waterfall Logic
  - 15/20/50/15 profit waterfall with Tiered Vault
  - Heartbeat monitoring & Legacy Protocol trigger
  - PostgreSQL + JSONB state management
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.config import get_settings

settings = get_settings()

# ── Logging ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── FastAPI Application ─────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description=(
        "A 100% autonomous, multi-agent AI wealth engine with a recursive "
        "growth model, tiered vault architecture, and generational wealth transfer."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS (permissive for development, locked down in Phase 5) ───────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount API routers ──────────────────────────────────────────────────
app.include_router(v1_router)


# ── Health check ────────────────────────────────────────────────────────
@app.get("/health", tags=["system"])
async def health_check():
    """System health check for load balancers and monitoring."""
    return {
        "status": "healthy",
        "engine": settings.app_title,
        "version": settings.app_version,
        "phase": "3A — Infrastructure & Multi-Tenancy",
    }


@app.on_event("startup")
async def startup_event():
    logger.info(
        "🌳 %s v%s starting — Phase 3C: The Watcher, Real Agents & Scheduler",
        settings.app_title,
        settings.app_version,
    )
    from app.services.scheduler import get_scheduler
    scheduler = get_scheduler()
    await scheduler.start()


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🌳 Engine shutting down gracefully.")
    from app.services.scheduler import get_scheduler
    scheduler = get_scheduler()
    await scheduler.stop()
