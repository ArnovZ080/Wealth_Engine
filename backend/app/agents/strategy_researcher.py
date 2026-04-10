"""
Strategy Researcher Agent — Performance analysis and genetic strategy iteration.

Matches Master Document §3 (Researcher Agent).
"""

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Dict, Any, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tree import Tree
from app.models.seed import Seed
from app.models.trade_decision import TradeDecision
from app.models.user import User

logger = logging.getLogger(__name__)

class StrategyResearcher:
    """
    Evaluates trading DNA and proposes Genetic Upgrades.
    """

    async def run_analysis(self, session: AsyncSession):
        """
        Global entry point for the weekly analysis loop.
        """
        logger.info("RESEARCHER: Running global strategy performance analysis...")
        
        # Fetch all active users
        res = await session.execute(select(User).where(User.is_active == True))
        users = res.scalars().all()
        
        for user in users:
            try:
                report = await self.generate_weekly_report(session, user.id)
                logger.info("RESEARCHER: Generated report for %s. Pruning suggestions: %d", 
                            user.display_name, len(report.get("pruning_suggestions", [])))
                # In Step 8, we'll notify the user/master via Telegram
            except Exception as e:
                logger.error("RESEARCHER: Failed analysis for user %s: %s", user.id, e)

    async def generate_weekly_report(self, session: AsyncSession, user_id: str) -> Dict[str, Any]:
        """
        Analyze performance and compare Dumb Mode vs LLM for a specific user.
        """
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        
        # 1. Fetch all closed trades for this user in last 30 days
        # We join with Seed then Tree then User to filter by user_id
        res = await session.execute(
            select(TradeDecision)
            .join(Seed)
            .join(Tree)
            .where(Tree.user_id == user_id)
            .where(TradeDecision.status == "closed")
            .where(TradeDecision.exit_timestamp >= thirty_days_ago)
        )
        trades = res.scalars().all()
        
        if not trades:
            return {
                "period": "30 days",
                "total_trades": 0,
                "msg": "Insufficient data for analysis."
            }

        # 2. Performance Breakdown: Dumb vs LLM
        # dumb_mode_agreed = True means LLM went with the technical indicator signal.
        # dumb_mode_agreed = False means LLM vetoed or refined a signal into a trade.
        
        counts = {"agreed": 0, "refined": 0}
        pnl = {"agreed": Decimal("0"), "refined": Decimal("0")}
        wins = {"agreed": 0, "refined": 0}
        
        for t in trades:
            key = "agreed" if t.dumb_mode_agreed else "refined"
            counts[key] += 1
            pnl[key] += (t.realized_pnl or Decimal("0"))
            if (t.realized_pnl or Decimal("0")) > 0:
                wins[key] += 1

        stats = {
            "agreed": {
                "count": counts["agreed"],
                "pnl": pnl["agreed"],
                "win_rate": wins["agreed"] / counts["agreed"] if counts["agreed"] > 0 else 0
            },
            "refined": {
                "count": counts["refined"],
                "pnl": pnl["refined"],
                "win_rate": wins["refined"] / counts["refined"] if counts["refined"] > 0 else 0
            }
        }

        # 3. Identify seeds for Genetic Pruning
        # If a seed has > 5 trades and refined pnl < 0 while agreed pnl > 0 for others...
        # Or if LLM is consistently losing money where technicals suggest otherwise.
        pruning = await self.check_genetic_pruning(session, user_id, trades)

        return {
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_trades": len(trades),
            "performance": stats,
            "pruning_suggestions": pruning,
            "recommendation": "Maintain" if stats["refined"]["win_rate"] >= 0.5 else "Prune refined strategies"
        }

    async def check_genetic_pruning(self, session: AsyncSession, user_id: str, trades: List[TradeDecision]) -> List[str]:
        """
        Spot seeds where LLM-refined strategies are underperforming the baseline.
        """
        # Logic: Groups trades by seed_id and check if refined ones are toxic
        seed_stats = {}
        for t in trades:
            if t.seed_id not in seed_stats:
                seed_stats[t.seed_id] = {"agreed_pnl": Decimal("0"), "refined_pnl": Decimal("0"), "refined_count": 0}
            
            if t.dumb_mode_agreed:
                seed_stats[t.seed_id]["agreed_pnl"] += (t.realized_pnl or Decimal("0"))
            else:
                seed_stats[t.seed_id]["refined_pnl"] += (t.realized_pnl or Decimal("0"))
                seed_stats[t.seed_id]["refined_count"] += 1

        toxic_seeds = []
        for sid, s in seed_stats.items():
            if s["refined_count"] >= 3 and s["refined_pnl"] < -100: # Toxicity threshold
                toxic_seeds.append(sid)
        
        return toxic_seeds
