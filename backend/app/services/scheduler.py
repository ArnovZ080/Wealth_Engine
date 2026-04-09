"""
Trading Scheduler — Background task runner.

Handles autonomous trading cycles, position monitoring, and heartbeat checks.
"""

import asyncio
import logging
from datetime import datetime, timezone
import os

from sqlalchemy import select
from app.database import async_session_factory
from app.services.seed_orchestrator import SeedOrchestrator
from app.services.position_monitor import PositionMonitor
from app.services.heartbeat import check_inactivity
from app.models.user import User

logger = logging.getLogger(__name__)

class TradingScheduler:
    """
    Background scheduler using asyncio tasks.
    """

    def __init__(self):
        self.running = False
        self._tasks = []
        self.enabled = os.environ.get("SCHEDULER_ENABLED", "true").lower() == "true"
        self._last_run = {
            "trading_cycle": None,
            "position_monitor": None,
            "heartbeat_check": None
        }

    async def start(self):
        """
        Start the background loops.
        """
        if not self.enabled:
            logger.warning("Scheduler is DISABLED via environment variable.")
            return

        if self.running:
            logger.warning("Scheduler is already running.")
            return

        self.running = True
        logger.info("Starting Trading Scheduler loops...")
        
        self._tasks = [
            asyncio.create_task(self._trading_cycle_loop()),
            asyncio.create_task(self._position_monitor_loop()),
            asyncio.create_task(self._heartbeat_check_loop()),
        ]

    async def stop(self):
        """
        Gracefully stop the loops.
        """
        self.running = False
        logger.info("Stopping Trading Scheduler...")
        for task in self._tasks:
            task.cancel()
        
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks = []

    async def get_status(self):
        """
        Returns the health status of the scheduler.
        """
        return {
            "running": self.running,
            "enabled": self.enabled,
            "tasks": [t.get_name() for t in self._tasks],
            "last_run": self._last_run
        }

    async def _trading_cycle_loop(self):
        """
        Run trading cycles for all users every 4 hours.
        """
        while self.running:
            logger.info("SCHEDULER: Triggering global trading cycle...")
            try:
                async with async_session_factory() as session:
                    orchestrator = SeedOrchestrator()
                    await orchestrator.run_all_users(session)
                    await session.commit()
                self._last_run["trading_cycle"] = datetime.now(timezone.utc).isoformat()
            except Exception as e:
                logger.error("Error in trading cycle loop: %s", e)
            
            # Sleep for 4 hours
            await asyncio.sleep(4 * 60 * 60)

    async def _position_monitor_loop(self):
        """
        Check positions every 5 minutes.
        """
        while self.running:
            logger.info("SCHEDULER: Triggering position monitoring...")
            try:
                async with async_session_factory() as session:
                    monitor = PositionMonitor()
                    await monitor.check_all_positions(session)
                    await session.commit()
                self._last_run["position_monitor"] = datetime.now(timezone.utc).isoformat()
            except Exception as e:
                logger.error("Error in position monitor loop: %s", e)
            
            # Sleep for 5 minutes
            await asyncio.sleep(5 * 60)

    async def _heartbeat_check_loop(self):
        """
        Check all users for heartbeat inactivity daily.
        """
        while self.running:
            logger.info("SCHEDULER: Triggering daily heartbeat checks...")
            try:
                async with async_session_factory() as session:
                    # Fetch all active users
                    res = await session.execute(select(User).where(User.is_active == True))
                    users = res.scalars().all()
                    
                    for user in users:
                        # In Phase 3A, check_inactivity needs to handle being called for many users.
                        # For now, we'll iterate. 
                        # Note: heartbeat.py might need a refactor if it's still using GlobalState.
                        try:
                            # Simple logic for now: we'll call it for each user if we can 
                            # or just log it. Real Legacy Protocol trigger is a Phase 5 item.
                            pass
                        except Exception as user_e:
                            logger.error("Error checking heartbeat for user %s: %s", user.id, user_e)
                
                self._last_run["heartbeat_check"] = datetime.now(timezone.utc).isoformat()
            except Exception as e:
                logger.error("Error in heartbeat check loop: %s", e)
            
            # Sleep for 24 hours
            await asyncio.sleep(24 * 60 * 60)

# Singleton instance
_scheduler_instance = TradingScheduler()

def get_scheduler():
    return _scheduler_instance
