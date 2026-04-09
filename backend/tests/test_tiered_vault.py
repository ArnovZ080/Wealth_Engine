"""
Dedicated test suite for apply_tiered_vault() logic.

Tests the Liquidity Ladder routing (Master Document §1.2):
  - Tier 2 fills before Tier 3
  - Exact overflow calculation
  - Edge cases: zero amount, exact capacity, already over capacity
"""

from decimal import Decimal

import pytest

from app.services.waterfall import apply_tiered_vault
from app.services.state_manager import get_global_state


@pytest.mark.asyncio
async def test_full_amount_to_tier2_when_ample_capacity(session):
    """
    Given: Tier 2 at $0, capacity $50,000.
    When: $500 vault allocation.
    Expected: $500 → Tier 2, $0 → Tier 3, not saturated.
    """
    state = await get_global_state(session, for_update=True)

    result = await apply_tiered_vault(session, Decimal("500"), state)

    assert result.tier2_deposit == Decimal("500.00000000")
    assert result.tier3_deposit == Decimal("0")
    assert result.tier2_saturated is False
    assert result.tier2_remaining_after == Decimal("49500")


@pytest.mark.asyncio
async def test_partial_overflow_to_tier3(session):
    """
    Given: Tier 2 at $49,800, capacity $50,000 → $200 remaining.
    When: $500 vault allocation.
    Expected: $200 → Tier 2, $300 → Tier 3, saturated.
    """
    state = await get_global_state(session, for_update=True)
    state.vault_tier2_etfs = Decimal("49800")

    result = await apply_tiered_vault(session, Decimal("500"), state)

    assert result.tier2_deposit == Decimal("200.00000000")
    assert result.tier3_deposit == Decimal("300.00000000")
    assert result.tier2_saturated is True
    assert result.tier2_remaining_after == Decimal("0")


@pytest.mark.asyncio
async def test_tier2_already_saturated(session):
    """
    Given: Tier 2 already at $50,000 capacity.
    When: $500 vault allocation.
    Expected: $0 → Tier 2, $500 → Tier 3.
    """
    state = await get_global_state(session, for_update=True)
    state.vault_tier2_etfs = Decimal("50000")

    result = await apply_tiered_vault(session, Decimal("500"), state)

    assert result.tier2_deposit == Decimal("0")
    assert result.tier3_deposit == Decimal("500.00000000")
    assert result.tier2_saturated is True


@pytest.mark.asyncio
async def test_tier2_over_capacity(session):
    """
    Given: Tier 2 somehow exceeds capacity ($51,000 of $50,000).
    When: $500 vault allocation.
    Expected: $0 → Tier 2, $500 → Tier 3 (remaining capacity clamped to 0).
    """
    state = await get_global_state(session, for_update=True)
    state.vault_tier2_etfs = Decimal("51000")

    result = await apply_tiered_vault(session, Decimal("500"), state)

    assert result.tier2_deposit == Decimal("0")
    assert result.tier3_deposit == Decimal("500.00000000")
    assert result.tier2_saturated is True


@pytest.mark.asyncio
async def test_zero_amount(session):
    """
    Given: $0 vault allocation.
    Expected: $0 to both tiers, not saturated.
    """
    state = await get_global_state(session, for_update=True)

    result = await apply_tiered_vault(session, Decimal("0"), state)

    assert result.tier2_deposit == Decimal("0")
    assert result.tier3_deposit == Decimal("0")
    assert result.tier2_saturated is False


@pytest.mark.asyncio
async def test_exact_remaining_capacity(session):
    """
    Given: Exactly $200 remaining in Tier 2.
    When: Vault allocation = exactly $200.
    Expected: $200 → Tier 2, $0 → Tier 3, not saturated (boundary).
    """
    state = await get_global_state(session, for_update=True)
    state.vault_tier2_etfs = Decimal("49800")

    result = await apply_tiered_vault(session, Decimal("200"), state)

    assert result.tier2_deposit == Decimal("200.00000000")
    assert result.tier3_deposit == Decimal("0")
    assert result.tier2_saturated is False
    assert result.tier2_remaining_after == Decimal("0")


@pytest.mark.asyncio
async def test_fractional_overflow(session):
    """
    Given: $0.01 remaining in Tier 2.
    When: $100 vault allocation.
    Expected: $0.01 → Tier 2, $99.99 → Tier 3.
    """
    state = await get_global_state(session, for_update=True)
    state.vault_tier2_etfs = Decimal("49999.99")

    result = await apply_tiered_vault(session, Decimal("100"), state)

    assert result.tier2_deposit == Decimal("0.01000000")
    assert result.tier3_deposit == Decimal("99.99000000")
    assert result.tier2_saturated is True
