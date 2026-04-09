"""
Tests for KellyPositionSizer.
"""

import pytest
from decimal import Decimal
from app.services.position_sizing import KellyPositionSizer

def test_kelly_sizing_basic():
    # b = 2 (2% profit target / 1% stop loss)
    # p = 0.6 (60% confidence)
    # q = 0.4
    # kelly_raw = (2 * 0.6 - 0.4) / 2 = 0.4
    # fractional_kelly (0.25) = 0.1 (10% max)
    
    seed_value = Decimal("100.00")
    entry = Decimal("100.00")
    target = Decimal("102.00")
    stop = Decimal("99.00")
    confidence = 0.6
    
    size = KellyPositionSizer.calculate(seed_value, entry, target, stop, confidence)
    
    # Fractional Kelly (0.25) * 0.4 = 0.1
    # 10% of $100 = $10
    assert size == Decimal("10.00")

def test_kelly_sizing_min_clamp():
    # Low confidence, expected small size clamped to 1%
    seed_value = Decimal("100.00")
    entry = Decimal("100.00")
    target = Decimal("101.00")
    stop = Decimal("99.00")
    confidence = 0.51 # Very low edge
    
    size = KellyPositionSizer.calculate(seed_value, entry, target, stop, confidence)
    assert size == Decimal("1.00") # Min clamp (1%)

def test_kelly_sizing_max_clamp():
    # Extreme edge, expected large size clamped to 10%
    seed_value = Decimal("100.00")
    entry = Decimal("100.00")
    target = Decimal("110.00")
    stop = Decimal("99.00")
    confidence = 0.9
    
    size = KellyPositionSizer.calculate(seed_value, entry, target, stop, confidence)
    assert size == Decimal("10.00") # Max clamp (10%)

def test_kelly_no_edge():
    # Zero edge
    seed_value = Decimal("100.00")
    entry = Decimal("100.00")
    target = Decimal("101.00")
    stop = Decimal("99.00")
    confidence = 0.4 # Less than 50% for 1:1
    
    size = KellyPositionSizer.calculate(seed_value, entry, target, stop, confidence)
    assert size == Decimal("0.00")
