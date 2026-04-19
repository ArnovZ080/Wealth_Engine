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
from app.models.forest import UserForestState
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
        # Nursery threshold check — plant new seeds if balance >= ZAR 1,000
        await self._check_and_plant_nursery_seeds(user_id, session)

        await session.commit()
        logger.info("Cycle complete for user %s: %s", user_id, summary)
        return summary

    async def _check_and_plant_nursery_seeds(self, user_id, session: AsyncSession):
        """Plant new seeds from nursery balance when ZAR 1,000 threshold is reached."""
        try:
            from app.services.forex_service import ForexService
            from decimal import Decimal
            from datetime import datetime
            forex = ForexService()
            usd_zar_rate = await forex.get_usd_to_zar()
            seed_cost_usd = Decimal("1000") / usd_zar_rate
            stop_loss_usd = Decimal("850") / usd_zar_rate

            forest_result = await session.execute(
                select(UserForestState).where(UserForestState.user_id == user_id)
            )
            forest_state = forest_result.scalar_one_or_none()
            if not forest_state:
                return

            seeds_planted = 0
            while forest_state.shared_nursery_balance >= seed_cost_usd:
                tree_result = await session.execute(
                    select(Tree).where(Tree.user_id == user_id, Tree.status == "active")
                )
                tree = tree_result.scalars().first()
                if not tree:
                    tree = Tree(
                        tree_id=f"TREE-{str(user_id)[:8]}-{int(datetime.utcnow().timestamp())}",
                        user_id=user_id,
                        status="active",
                        active_seeds_count=0,
                        max_seeds=100,
                        preflight_passed=True,
                    )
                    session.add(tree)
                    await session.flush()

                import uuid as _uuid
                seed = Seed(
                    seed_id=f"SEED-{str(_uuid.uuid4())[:8].upper()}",
                    tree_id=tree.id,
                    initial_value=seed_cost_usd,
                    current_value=seed_cost_usd,
                    stop_loss_floor=stop_loss_usd,
                    status="active",
                )
                session.add(seed)
                tree.active_seeds_count += 1
                forest_state.shared_nursery_balance -= seed_cost_usd
                seeds_planted += 1
                await session.flush()

            if seeds_planted > 0:
                logger.info("Planted %d new seeds for user %s", seeds_planted, user_id)
        except Exception as e:
            logger.error("Error planting nursery seeds: %s", e)

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
