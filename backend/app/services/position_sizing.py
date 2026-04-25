"""
Kelly Position Sizer — Fractional Kelly Criterion (0.25x).

Calculates optimal position sizes based on reward/risk and confidence.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

class KellyPositionSizer:
    """
    Implements Fractional Kelly Criterion (0.25x) from Master Doc §1.3.
    f* = 0.25 * (b*p - q) / b
    where:
        b = reward/risk ratio (target_exit - entry) / (entry - stop_loss)
        p = probability of winning (from confidence score)
        q = 1 - p
    """

    KELLY_FRACTION = Decimal("0.25")
    MAX_POSITION_PCT = Decimal("0.10")   # Never exceed 10% of seed value
    MIN_POSITION_PCT = Decimal("0.01")   # Minimum 1% to be worth the trade

    @classmethod
    def calculate(
        self,
        seed_value: Decimal,
        entry_price: Decimal,
        target_exit: Decimal,
        stop_loss: Decimal,
        confidence: float  # 0.0 to 1.0
    ) -> Decimal:
        """
        Returns the dollar amount to allocate to this position.
        """
        # 1. Calculate reward/risk ratio (b)
        reward = target_exit - entry_price
        risk = entry_price - stop_loss
        
        # Guard against zero or negative risk (would be infinity or invalid trade)
        if risk <= 0 or risk != risk:  # zero, negative or NaN
            return Decimal("0")
        
        if reward <= 0:
            return Decimal("0")
            
        b = reward / risk
        
        # 2. Probability (p)
        # Cap probability at 0.95 to avoid extreme sizing on perfect confidence
        p = Decimal(str(min(max(confidence, 0.0), 0.95)))
        q = Decimal("1") - p
        
        # 3. Kelly formula: f* = (bp - q) / b
        kelly_raw = (b * p - q) / b
        
        if kelly_raw <= 0:
            return Decimal("0")
            
        # 4. Apply fractional Kelly
        kelly_fractional = self.KELLY_FRACTION * kelly_raw
        
        # 5. Apply Clamps
        position_pct = max(self.MIN_POSITION_PCT, min(kelly_fractional, self.MAX_POSITION_PCT))
        
        return (seed_value * position_pct).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
