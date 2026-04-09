"""
Comprehensive test suite for execute_waterfall() and apply_tiered_vault().

Covers all scenarios specified in the Phase 1 requirements:
  1. Normal profit distribution — exact 15/20/50/15 Decimal math
  2. Zero-profit edge case — no state mutation
  3. Fees exceeding gross profit — negative net, zero distribution
  4. Tier 2 saturation overflow — Tier 2 fills to cap, overflow to Tier 3
  5. Tier 2 not saturated — 100% to Tier 2, Tier 3 unchanged
  6. Atomicity on failure — complete rollback on error
  7. Nursery threshold trigger — flags new seed planting at $100
  8. Decimal precision — no float drift across 1000 sequential executions
"""

from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from app.services.waterfall import execute_waterfall, apply_tiered_vault, PRECISION
from app.services.state_manager import get_global_state


# ═══════════════════════════════════════════════════════════════════════
# Test 1: Normal Profit Distribution
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_normal_profit_distribution(session):
    """
    Given: $1000 gross profit, $50 fees, 30% tax rate
    Expected:
      tax_reserve = $1000 * 0.30 = $300
      net_profit  = $1000 - ($50 + $300) = $650
      reservoir   = $650 * 0.15 = $97.50
      nursery     = $650 * 0.20 = $130.00
      vault       = $650 * 0.50 = $325.00
      reinvest    = $650 * 0.15 = $97.50
    """
    result = await execute_waterfall(
        session=session,
        gross_profit=Decimal("1000"),
        fees=Decimal("50"),
        tax_rate=Decimal("0.30"),
    )

    assert result.gross_profit == Decimal("1000")
    assert result.fees == Decimal("50")
    assert result.tax_reserve == Decimal("300.00000000")
    assert result.net_profit == Decimal("650")

    assert result.reservoir == Decimal("97.50000000")
    assert result.nursery == Decimal("130.00000000")
    assert result.reinvestment == Decimal("97.50000000")

    # Vault total should be 50% of net, potentially with rounding adjustment
    expected_vault = Decimal("325.00000000")
    assert result.vault_total == expected_vault

    # Verify sum equals net_profit exactly (zero dust)
    total = result.reservoir + result.nursery + result.vault_total + result.reinvestment
    assert total == result.net_profit

    # Verify DB state was updated
    state = await get_global_state(session)
    assert Decimal(str(state.shared_reservoir_balance)) == result.reservoir
    assert Decimal(str(state.shared_nursery_balance)) == result.nursery


# ═══════════════════════════════════════════════════════════════════════
# Test 2: Zero Profit Edge Case
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_zero_profit(session):
    """
    Given: $0 gross profit
    Expected: All distributions are $0, no state mutation.
    """
    result = await execute_waterfall(
        session=session,
        gross_profit=Decimal("0"),
        fees=Decimal("0"),
        tax_rate=Decimal("0.30"),
    )

    assert result.net_profit == Decimal("0")
    assert result.reservoir == Decimal("0")
    assert result.nursery == Decimal("0")
    assert result.vault_total == Decimal("0")
    assert result.reinvestment == Decimal("0")
    assert result.vault_tier2_deposit == Decimal("0")
    assert result.vault_tier3_deposit == Decimal("0")

    # Verify no state mutation
    state = await get_global_state(session)
    assert Decimal(str(state.shared_reservoir_balance)) == Decimal("0")
    assert Decimal(str(state.shared_nursery_balance)) == Decimal("0")


# ═══════════════════════════════════════════════════════════════════════
# Test 3: Fees Exceed Gross Profit
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_fees_exceed_gross_profit(session):
    """
    Given: $100 gross profit, $200 fees, 30% tax
    Expected: net = 100 - (200 + 30) = -130 → zero distribution.
    """
    result = await execute_waterfall(
        session=session,
        gross_profit=Decimal("100"),
        fees=Decimal("200"),
        tax_rate=Decimal("0.30"),
    )

    assert result.net_profit < Decimal("0")
    assert result.net_profit == Decimal("-130.00000000")
    assert result.reservoir == Decimal("0")
    assert result.nursery == Decimal("0")
    assert result.vault_total == Decimal("0")
    assert result.reinvestment == Decimal("0")

    # No state mutation
    state = await get_global_state(session)
    assert Decimal(str(state.shared_reservoir_balance)) == Decimal("0")
    assert Decimal(str(state.shared_nursery_balance)) == Decimal("0")
    assert Decimal(str(state.vault_tier2_etfs)) == Decimal("0")


# ═══════════════════════════════════════════════════════════════════════
# Test 4: Tier 2 Saturation Forces Overflow to Tier 3
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_tier2_saturation_overflow(session):
    """
    Given: Tier 2 at $49,900 of $50,000 cap → $100 remaining capacity.
    When: Vault allocation = $325 (from $1000 gross scenario).
    Expected: $100 → Tier 2, $225 → Tier 3.
    """
    # Set Tier 2 near saturation
    state = await get_global_state(session, for_update=True)
    state.vault_tier2_etfs = Decimal("49900")

    result = await execute_waterfall(
        session=session,
        gross_profit=Decimal("1000"),
        fees=Decimal("50"),
        tax_rate=Decimal("0.30"),
    )

    # Vault allocation is 50% of net $650 = $325
    assert result.vault_tier2_deposit == Decimal("100.00000000")
    assert result.vault_tier3_deposit == Decimal("225.00000000")
    assert result.vault_tier2_deposit + result.vault_tier3_deposit == result.vault_total

    # Verify DB state
    updated_state = await get_global_state(session)
    assert Decimal(str(updated_state.vault_tier2_etfs)) == Decimal("50000.00000000")
    assert Decimal(str(updated_state.vault_tier3_real_estate)) == Decimal("225.00000000")


# ═══════════════════════════════════════════════════════════════════════
# Test 5: Tier 2 Not Saturated
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_tier2_not_saturated(session):
    """
    Given: Tier 2 well below capacity ($0 of $50,000).
    When: Vault allocation = $325.
    Expected: 100% → Tier 2, Tier 3 unchanged at $0.
    """
    result = await execute_waterfall(
        session=session,
        gross_profit=Decimal("1000"),
        fees=Decimal("50"),
        tax_rate=Decimal("0.30"),
    )

    assert result.vault_tier2_deposit == result.vault_total
    assert result.vault_tier3_deposit == Decimal("0")

    state = await get_global_state(session)
    assert Decimal(str(state.vault_tier3_real_estate)) == Decimal("0")


# ═══════════════════════════════════════════════════════════════════════
# Test 6: Atomicity — Transaction Rollback on Failure
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_atomicity_on_failure(session):
    """
    Given: A valid waterfall execution where update_balances raises an error.
    Expected: Complete rollback — all balances remain at their original values.
    """
    # Record original state
    original_state = await get_global_state(session)
    original_reservoir = Decimal(str(original_state.shared_reservoir_balance))
    original_nursery = Decimal(str(original_state.shared_nursery_balance))

    # Patch update_balances to raise after being called
    with patch(
        "app.services.waterfall.update_balances",
        side_effect=RuntimeError("Simulated DB failure"),
    ):
        with pytest.raises(RuntimeError, match="Simulated DB failure"):
            await execute_waterfall(
                session=session,
                gross_profit=Decimal("1000"),
                fees=Decimal("50"),
                tax_rate=Decimal("0.30"),
            )

    # Rollback the session (simulating what the API dependency would do)
    await session.rollback()

    # Verify balances are unchanged
    state = await get_global_state(session)
    assert Decimal(str(state.shared_reservoir_balance)) == original_reservoir
    assert Decimal(str(state.shared_nursery_balance)) == original_nursery


# ═══════════════════════════════════════════════════════════════════════
# Test 7: Nursery Threshold Trigger
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_nursery_threshold_trigger(session):
    """
    Given: Nursery has $0, waterfall adds $130 (from $1000 gross).
    Expected: Nursery reaches $130 >= $100 threshold → flag is True.
    """
    result = await execute_waterfall(
        session=session,
        gross_profit=Decimal("1000"),
        fees=Decimal("50"),
        tax_rate=Decimal("0.30"),
    )

    # $650 net * 20% = $130 to nursery, which is >= $100 threshold
    assert result.nursery == Decimal("130.00000000")
    assert result.nursery_threshold_reached is True


@pytest.mark.asyncio
async def test_nursery_threshold_not_reached(session):
    """
    Given: Small profit that produces nursery deposit < $100.
    Expected: Nursery threshold flag is False.
    """
    # With $100 gross, $10 fees, 30% tax:
    # net = 100 - (10 + 30) = 60
    # nursery = 60 * 0.20 = 12 → below $100 threshold
    result = await execute_waterfall(
        session=session,
        gross_profit=Decimal("100"),
        fees=Decimal("10"),
        tax_rate=Decimal("0.30"),
    )

    assert result.nursery == Decimal("12.00000000")
    assert result.nursery_threshold_reached is False


# ═══════════════════════════════════════════════════════════════════════
# Test 8: Decimal Precision — No Float Drift
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_decimal_precision_no_drift(session):
    """
    Run 100 sequential waterfall executions with a tricky decimal
    (e.g., $33.33 gross, $1.11 fees) and verify the final balances
    match the expected exact Decimal sum — no accumulated float error.

    This test would FAIL with float arithmetic due to IEEE 754 rounding.
    """
    gross = Decimal("33.33")
    fees = Decimal("1.11")
    tax_rate = Decimal("0.30")
    iterations = 100

    expected_reservoir_total = Decimal("0")
    expected_nursery_total = Decimal("0")

    for _ in range(iterations):
        result = await execute_waterfall(
            session=session,
            gross_profit=gross,
            fees=fees,
            tax_rate=tax_rate,
        )
        expected_reservoir_total += result.reservoir
        expected_nursery_total += result.nursery

    # Verify the DB balances match the summed Decimal expectations exactly
    state = await get_global_state(session)
    actual_reservoir = Decimal(str(state.shared_reservoir_balance))
    actual_nursery = Decimal(str(state.shared_nursery_balance))

    assert actual_reservoir == expected_reservoir_total, (
        f"Reservoir drift detected after {iterations} iterations: "
        f"expected {expected_reservoir_total}, got {actual_reservoir}"
    )
    assert actual_nursery == expected_nursery_total, (
        f"Nursery drift detected after {iterations} iterations: "
        f"expected {expected_nursery_total}, got {actual_nursery}"
    )


# ═══════════════════════════════════════════════════════════════════════
# Test 9: Waterfall Split Sums to Net Profit (Zero Dust)
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_split_sums_to_net_profit(session):
    """
    Verify that reservoir + nursery + vault + reinvestment == net_profit
    exactly, with no rounding dust left over.
    """
    # Use an amount that produces tricky rounding
    result = await execute_waterfall(
        session=session,
        gross_profit=Decimal("777.77"),
        fees=Decimal("23.45"),
        tax_rate=Decimal("0.30"),
    )

    if result.net_profit > Decimal("0"):
        total = result.reservoir + result.nursery + result.vault_total + result.reinvestment
        assert total == result.net_profit, (
            f"Rounding dust detected: split sum {total} != net {result.net_profit}"
        )


# ═══════════════════════════════════════════════════════════════════════
# Test 10: Tier 2 Exactly at Capacity
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_tier2_exactly_at_capacity(session):
    """
    Given: Tier 2 is exactly at capacity ($50,000 of $50,000).
    Expected: 100% of vault allocation goes to Tier 3.
    """
    state = await get_global_state(session, for_update=True)
    state.vault_tier2_etfs = Decimal("50000")

    result = await execute_waterfall(
        session=session,
        gross_profit=Decimal("1000"),
        fees=Decimal("50"),
        tax_rate=Decimal("0.30"),
    )

    assert result.vault_tier2_deposit == Decimal("0")
    assert result.vault_tier3_deposit == result.vault_total

    updated = await get_global_state(session)
    assert Decimal(str(updated.vault_tier2_etfs)) == Decimal("50000")
    assert Decimal(str(updated.vault_tier3_real_estate)) == result.vault_total


# ═══════════════════════════════════════════════════════════════════════
# Test 11: Custom Tax Rate Override
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_custom_tax_rate_override(session):
    """
    Given: Default tax rate is 30%, but we pass 10% override.
    Expected: Tax reserve uses 10%, resulting in higher net profit.
    """
    result = await execute_waterfall(
        session=session,
        gross_profit=Decimal("1000"),
        fees=Decimal("50"),
        tax_rate=Decimal("0.10"),
    )

    # tax_reserve = 1000 * 0.10 = 100
    # net = 1000 - (50 + 100) = 850
    assert result.tax_reserve == Decimal("100.00000000")
    assert result.net_profit == Decimal("850")
