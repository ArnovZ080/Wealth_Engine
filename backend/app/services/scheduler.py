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

    async def _deposit_scan_loop(self):
        """
        Scan for new deposits via Investec API every 30 mins during business hours.
        """
        from app.services.deposit_detector import DepositDetector
        while self.running:
            try:
                # Business hours SAST (UTC+2)
                # For simplicity, we just check local hour if server is in same timezone 
                # or use a proper timezone check.
                # Assume 6am-8pm SAST
                now = datetime.now(timezone.utc)
                hour_sast = (now.hour + 2) % 24
                
                if 6 <= hour_sast <= 20:
                    logger.info("SCHEDULER: Scanning for Investec deposits...")
                    async with async_session_factory() as session:
                        detector = DepositDetector()
                        new_deps = await detector.scan_for_deposits(session)
                        if new_deps:
                            logger.info("SCHEDULER: Detected %d new deposits.", len(new_deps))
                
                self._last_run["deposit_scan"] = datetime.now(timezone.utc).isoformat()
            except Exception as e:
                logger.error("Error in deposit scan loop: %s", e)
            
            await asyncio.sleep(30 * 60)

    async def _research_loop(self):
        """
        Run Strategy Researcher analysis weekly (Sunday 2am SAST).
        """
        from app.agents.strategy_researcher import StrategyResearcher
        while self.running:
            try:
                now = datetime.now(timezone.utc)
                hour_sast = (now.hour + 2) % 24
                # Sunday = 6 in weekday()
                if now.weekday() == 6 and hour_sast == 2:
                    logger.info("SCHEDULER: Triggering weekly strategy research...")
                    async with async_session_factory() as session:
                        researcher = StrategyResearcher()
                        await researcher.run_analysis(session)
                    self._last_run["strategy_research"] = datetime.now(timezone.utc).isoformat()
            except Exception as e:
                logger.error("Error in research loop: %s", e)
            
            # Check hourly
            await asyncio.sleep(60 * 60)

    async def _heartbeat_check_loop(self):
        """
        Check all users for heartbeat inactivity and process auto-payouts daily.
        """
        from app.services.cashout_service import CashOutService
        while self.running:
            logger.info("SCHEDULER: Triggering daily heartbeat checks and auto-payouts...")
            try:
                async with async_session_factory() as session:
                    # 1. Payout Processing
                    cashout = CashOutService()
                    await cashout.process_pending_withdrawals(session)
                    
                    # 2. Heartbeat checks
                    res = await session.execute(select(User).where(User.is_active == True))
                    users = res.scalars().all()
                    for user in users:
                        try:
                            # In Phase 5, we can actually trigger the Legacy Protocol 
                            # if inactivity exceeds thresholds.
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
