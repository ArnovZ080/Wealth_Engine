"""
Waterfall Service — The 15/20/50/15 Profit Distribution Engine.

Implements Master Document §1.1 (4-Way Profit Waterfall) and §1.2 (Tiered Vault).

Critical Design Invariants:
  1. ALL monetary math uses Python Decimal — never float.
  2. The entire distribution is ATOMIC — any failure rolls back every balance change.
  3. Tier 2 (ETFs) fills to capacity before any overflow reaches Tier 3 (Real Estate).
  4. Net profit ≤ 0 results in a zero-distribution (no state mutation).

Usage:
    async with async_session_factory() as session:
        result = await execute_waterfall(session, gross_profit, fees, tax_rate)
"""

import logging
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.global_state import GlobalState
from app.services.state_manager import (
    get_global_state,
    get_vault_tier2_remaining_capacity,
    update_balances,
)

logger = logging.getLogger(__name__)
settings = get_settings()

# Canonical precision: 8 decimal places, matching NUMERIC(20,8) in the DB
PRECISION = Decimal("0.00000001")


@dataclass(frozen=True)
class TieredVaultResult:
    """Immutable result of the Tiered Vault routing decision."""

    tier2_deposit: Decimal
    tier3_deposit: Decimal
    tier2_remaining_after: Decimal
    tier2_saturated: bool


@dataclass(frozen=True)
class WaterfallResult:
    """Immutable result of a complete waterfall execution."""

    gross_profit: Decimal
    fees: Decimal
    tax_reserve: Decimal
    net_profit: Decimal
    reservoir: Decimal
    nursery: Decimal
    vault_total: Decimal
    vault_tier2_deposit: Decimal
    vault_tier3_deposit: Decimal
    reinvestment: Decimal
    nursery_threshold_reached: bool


async def apply_tiered_vault(
    session: AsyncSession,
    amount: Decimal,
    state: GlobalState,
) -> TieredVaultResult:
    """
    Route the vault allocation through the Liquidity Ladder.

    Master Document §1.2:
      - Tier 2 (ETFs) fills to vault_tier2_capacity before overflow
      - Only overflow reaches Tier 3 (Real Estate)

    Args:
        session: Active DB session (within transaction).
        amount: Total vault allocation (50% of net profit).
        state: GlobalState with for_update lock held.

    Returns:
        TieredVaultResult with exact deposit amounts per tier.
    """
    remaining_capacity = await get_vault_tier2_remaining_capacity(session, state)

    if amount <= remaining_capacity:
        # Tier 2 has room — entire amount goes to ETFs
        tier2_deposit = amount.quantize(PRECISION, rounding=ROUND_HALF_UP)
        tier3_deposit = Decimal("0")
        tier2_remaining_after = remaining_capacity - tier2_deposit
        tier2_saturated = False
    else:
        # Tier 2 overflow — fill to cap, remainder flows to Tier 3
        tier2_deposit = remaining_capacity.quantize(PRECISION, rounding=ROUND_HALF_UP)
        tier3_deposit = (amount - remaining_capacity).quantize(PRECISION, rounding=ROUND_HALF_UP)
        tier2_remaining_after = Decimal("0")
        tier2_saturated = True

    logger.info(
        "Tiered Vault routing: amount=%s → Tier2=%s, Tier3=%s (saturated=%s)",
        amount,
        tier2_deposit,
        tier3_deposit,
        tier2_saturated,
    )

    return TieredVaultResult(
        tier2_deposit=tier2_deposit,
        tier3_deposit=tier3_deposit,
        tier2_remaining_after=tier2_remaining_after,
        tier2_saturated=tier2_saturated,
    )


async def execute_waterfall(
    session: AsyncSession,
    gross_profit: Decimal,
    fees: Decimal,
    tax_rate: Decimal | None = None,
    seed_id: str | None = None,
) -> WaterfallResult:
    """
    Execute the atomic 15/20/50/15 waterfall profit distribution.

    Master Document §1.1 & §9.3:
      Net Profit = Gross Profit − (Trading Fees + Tax Reserve)
      Reservoir:    15% of Net Profit  (Tier 1 — BUIDL / T-Bills)
      Nursery:      20% of Net Profit  (USDC stablecoin pool)
      Vault:        50% of Net Profit  (Tiered: ETFs → Real Estate)
      Reinvestment: 15% of Net Profit  (Back into active seed)

    Atomicity Guarantee:
      The entire function operates within the caller's session transaction.
      If any step raises an exception, SQLAlchemy's session rollback ensures
      zero state mutation. The state row is locked via SELECT FOR UPDATE
      to prevent concurrent waterfall executions from racing.

    Args:
        session: Active async session. The caller MUST manage commit/rollback.
        gross_profit: Gross profit from the closed trade.
        fees: Total trading fees.
        tax_rate: Override tax rate. If None, uses the stored default.
        seed_id: Optional seed ID for reinvestment tracking.

    Returns:
        WaterfallResult with exact distribution breakdown.

    Raises:
        Exception: Any DB or arithmetic error triggers full rollback.
    """
    # ── Acquire exclusive lock on global state ──────────────────────────
    state = await get_global_state(session, for_update=True)

    # ── Resolve tax rate ────────────────────────────────────────────────
    effective_tax_rate = tax_rate if tax_rate is not None else Decimal(str(state.tax_rate))

    # ── Compute net profit ──────────────────────────────────────────────
    tax_reserve = (gross_profit * effective_tax_rate).quantize(PRECISION, rounding=ROUND_HALF_UP)
    net_profit = gross_profit - (fees + tax_reserve)

    logger.info(
        "Waterfall: gross=%s, fees=%s, tax_reserve=%s, net=%s",
        gross_profit,
        fees,
        tax_reserve,
        net_profit,
    )

    # ── Zero or negative net profit — no distribution ───────────────────
    if net_profit <= Decimal("0"):
        logger.info("Net profit ≤ 0 (%s). Zero distribution — no state mutation.", net_profit)
        return WaterfallResult(
            gross_profit=gross_profit,
            fees=fees,
            tax_reserve=tax_reserve,
            net_profit=net_profit,
            reservoir=Decimal("0"),
            nursery=Decimal("0"),
            vault_total=Decimal("0"),
            vault_tier2_deposit=Decimal("0"),
            vault_tier3_deposit=Decimal("0"),
            reinvestment=Decimal("0"),
            nursery_threshold_reached=False,
        )

    # ── Compute the 15/20/50/15 split ──────────────────────────────────
    reservoir_amount = (net_profit * settings.waterfall_reservoir_pct).quantize(
        PRECISION, rounding=ROUND_HALF_UP
    )
    nursery_amount = (net_profit * settings.waterfall_nursery_pct).quantize(
        PRECISION, rounding=ROUND_HALF_UP
    )
    vault_amount = (net_profit * settings.waterfall_vault_pct).quantize(
        PRECISION, rounding=ROUND_HALF_UP
    )
    reinvestment_amount = (net_profit * settings.waterfall_reinvestment_pct).quantize(
        PRECISION, rounding=ROUND_HALF_UP
    )

    # ── Rounding reconciliation ─────────────────────────────────────────
    # Due to quantization, the four splits may not sum exactly to net_profit.
    # We absorb the rounding remainder into the vault (largest bucket) to
    # ensure zero-dust accounting. This is a design decision documented in
    # the Phase 1 summary.
    distributed_total = reservoir_amount + nursery_amount + vault_amount + reinvestment_amount
    rounding_remainder = net_profit - distributed_total
    vault_amount += rounding_remainder

    logger.info(
        "Split: reservoir=%s, nursery=%s, vault=%s, reinvest=%s (rounding_adj=%s)",
        reservoir_amount,
        nursery_amount,
        vault_amount,
        reinvestment_amount,
        rounding_remainder,
    )

    # ── Apply Tiered Vault logic ────────────────────────────────────────
    vault_result = await apply_tiered_vault(session, vault_amount, state)

    # ── Update balances atomically ──────────────────────────────────────
    await update_balances(
        session,
        state,
        reservoir_delta=reservoir_amount,
        nursery_delta=nursery_amount,
        vault_tier2_delta=vault_result.tier2_deposit,
        vault_tier3_delta=vault_result.tier3_deposit,
    )

    # ── Route Reinvestment to Seed ──────────────────────────────────────
    if seed_id and reinvestment_amount > 0:
        from app.models.seed import Seed
        seed_stmt = select(Seed).where(Seed.seed_id == seed_id).with_for_update()
        seed_result = await session.execute(seed_stmt)
        target_seed = seed_result.scalar_one_or_none()
        
        if target_seed:
            target_seed.current_value += reinvestment_amount
            logger.info("Reinvested $%s into seed %s (new value: $%s)", 
                        reinvestment_amount, seed_id, target_seed.current_value)
        else:
            logger.warning("Seed %s not found for reinvestment. Funds held in limbo or default routing needed.", seed_id)
            # Default routing: if seed not found, we could pool it back to Reservoir or Nursery.
            # For now, we log a warning.

    # ── Check nursery threshold (Master Document §9.3) ──────────────────
    # If nursery >= $100, a new seed should be planted.
    # Phase 1: we flag it. Phase 2: the Nursery actually plants seeds.
    current_nursery = Decimal(str(state.shared_nursery_balance))
    nursery_threshold_reached = current_nursery >= settings.nursery_seed_threshold

    if nursery_threshold_reached:
        logger.info(
            "Nursery threshold reached: $%s >= $%s — new seed planting flagged",
            current_nursery,
            settings.nursery_seed_threshold,
        )

    # ── Log the transaction ─────────────────────────────────────────────
    # Transaction logging is handled by the DB session commit and the
    # waterfall result dataclass. Detailed audit logging will be added
    # in Phase 2 with the Accountant Agent.
    logger.info(
        "Waterfall complete — Reservoir: +$%s, Nursery: +$%s, "
        "Vault T2: +$%s, Vault T3: +$%s, Reinvest: $%s",
        reservoir_amount,
        nursery_amount,
        vault_result.tier2_deposit,
        vault_result.tier3_deposit,
        reinvestment_amount,
    )

    return WaterfallResult(
        gross_profit=gross_profit,
        fees=fees,
        tax_reserve=tax_reserve,
        net_profit=net_profit,
        reservoir=reservoir_amount,
        nursery=nursery_amount,
        vault_total=vault_amount,
        vault_tier2_deposit=vault_result.tier2_deposit,
        vault_tier3_deposit=vault_result.tier3_deposit,
        reinvestment=reinvestment_amount,
        nursery_threshold_reached=nursery_threshold_reached,
    )
