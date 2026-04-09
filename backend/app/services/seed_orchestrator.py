"""
Seed Orchestrator — The Root Orchestrator execution loop.

Sequentially processes all active seeds for all users or a specific user.
"""

import logging
from typing import Dict, List, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.models.seed import Seed, SeedStatus
from app.models.tree import Tree, TreeStatus
from app.services.trade_pipeline import TradePipeline
from app.services.indicator_service import IndicatorService
from app.exchanges.connector_factory import ConnectorFactory

logger = logging.getLogger(__name__)

class SeedOrchestrator:
    """
    Coordinates the trading heartbeat.
    """

    def __init__(self):
        self.indicator_service = IndicatorService()
        self.connector_factory = ConnectorFactory()

    async def run_cycle(self, user_id: str, session: AsyncSession) -> Dict[str, Any]:
        """
        Execute one full trading cycle for a user.
        """
        logger.info("Starting trading cycle for user %s", user_id)
        
        # 1. Load active seeds for the user
        stmt = (
            select(Seed)
            .join(Tree)
            .where(
                Tree.user_id == user_id,
                Tree.status == TreeStatus.ACTIVE,
                Seed.status == SeedStatus.ACTIVE
            )
        )
        res = await session.execute(stmt)
        seeds = res.scalars().all()
        
        summary = {
            "user_id": user_id,
            "seeds_processed": 0,
            "trades_executed": 0,
            "trades_vetoed": 0,
            "errors": 0,
            "details": []
        }

        pipeline = TradePipeline(session, user_id, self.indicator_service, self.connector_factory)

        # 2. Sequential processing
        for seed in seeds:
            try:
                summary["seeds_processed"] += 1
                result = await pipeline.execute_for_seed(seed.id)
                
                if result:
                    summary["trades_executed"] += 1
                    summary["details"].append(f"Seed {seed.seed_id}: Executed {result.side} {result.symbol}")
                else:
                    summary["details"].append(f"Seed {seed.seed_id}: No trade executed")
                    
            except Exception as e:
                logger.error("Error processing seed %s: %s", seed.seed_id, e)
                summary["errors"] += 1
                summary["details"].append(f"Seed {seed.seed_id}: ERROR {str(e)}")

        # 3. Post-cycle Logic: Nursery Planting & Genetic Pruning
        # These are existing Phase 2/3A logic points we keep stubs for
        # nursery_balance check -> create new seed if >= $100
        # ROI check -> prune weakest seed
        
        await session.commit()
        logger.info("Cycle complete for user %s: %s", user_id, summary)
        return summary

    async def run_all_users(self, session: AsyncSession) -> Dict[str, Any]:
        """
        Run cycles for all active users. (Admin/Scheduler call)
        """
        stmt = select(User).where(User.is_active == True)
        res = await session.execute(stmt)
        users = res.scalars().all()
        
        aggregate = {
            "users_processed": 0,
            "total_trades": 0,
            "user_summaries": []
        }
        
        for user in users:
            summary = await self.run_cycle(user.id, session)
            aggregate["users_processed"] += 1
            aggregate["total_trades"] += summary["trades_executed"]
            aggregate["user_summaries"].append(summary)
            
        return aggregate
