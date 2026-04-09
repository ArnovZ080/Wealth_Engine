"""
Waterfall Service — Multi-Tenant 15/20/50/15 Profit Distribution.

Implements Phase 3A Platform Fees and Per-User Forest State routing.
"""

import logging
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.forest import UserForestState
from app.models.user import User, UserRole
from app.services.state_manager import (
    get_user_forest_state,
    get_master_forest_state,
    get_vault_tier2_remaining_capacity,
    update_balances,
)

logger = logging.getLogger(__name__)
settings = get_settings()

PRECISION = Decimal("0.00000001")

@dataclass(frozen=True)
class TieredVaultResult:
    tier2_deposit: Decimal
    tier3_deposit: Decimal
    tier2_remaining_after: Decimal
    tier2_saturated: bool

@dataclass(frozen=True)
class WaterfallResult:
    gross_profit: Decimal
    fees: Decimal
    tax_reserve: Decimal
    platform_fee: Decimal        # NEW: 5% fee for members
    net_profit_after_tax: Decimal
    distributable_profit: Decimal # profit after tax AND platform fee
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
    state: UserForestState,
) -> TieredVaultResult:
    """Route vault allocation through the user's Liquidity Ladder."""
    remaining_capacity = await get_vault_tier2_remaining_capacity(session, state)

    if amount <= remaining_capacity:
        tier2_deposit = amount.quantize(PRECISION, rounding=ROUND_HALF_UP)
        tier3_deposit = Decimal("0")
        tier2_remaining_after = remaining_capacity - tier2_deposit
        tier2_saturated = False
    else:
        tier2_deposit = remaining_capacity.quantize(PRECISION, rounding=ROUND_HALF_UP)
        tier3_deposit = (amount - remaining_capacity).quantize(PRECISION, rounding=ROUND_HALF_UP)
        tier2_remaining_after = Decimal("0")
        tier2_saturated = True

    return TieredVaultResult(
        tier2_deposit=tier2_deposit,
        tier3_deposit=tier3_deposit,
        tier2_remaining_after=tier2_remaining_after,
        tier2_saturated=tier2_saturated,
    )

async def execute_waterfall(
    session: AsyncSession,
    user: User,
    gross_profit: Decimal,
    fees: Decimal,
    tax_rate: Optional[Decimal] = None,
    seed_id: Optional[str] = None,
) -> WaterfallResult:
    """
    Execute the multi-tenant waterfall.
    
    1. Deduct tax -> Net Profit After Tax
    2. Deduct Platform Fee (credited to Master) -> Distributable Profit
    3. Split 15/20/50/15 on Distributable Profit
    """
    # ── 1. Acquire locks ────────────────────────────────────────────────
    # Lock the user's forest state
    state = await get_user_forest_state(session, user.id, for_update=True)
    
    # Lock the master state for platform fee crediting
    master_state = None
    if user.role != UserRole.MASTER:
        master_state = await get_master_forest_state(session, for_update=True)

    # ── 2. Tax & Net Profit ─────────────────────────────────────────────
    effective_tax_rate = tax_rate if tax_rate is not None else Decimal(str(settings.tax_rate))
    tax_reserve = (gross_profit * effective_tax_rate).quantize(PRECISION, rounding=ROUND_HALF_UP)
    net_profit_at = gross_profit - (fees + tax_reserve)

    if net_profit_at <= Decimal("0"):
        return _zero_result(gross_profit, fees, tax_reserve, net_profit_at)

    # ── 3. Platform Fee Deduction ──────────────────────────────────────
    # Fee flows to Master Reservoir
    fee_rate = Decimal(str(user.platform_fee_rate))
    platform_fee = (net_profit_at * fee_rate).quantize(PRECISION, rounding=ROUND_HALF_UP)
    distributable_profit = net_profit_at - platform_fee

    # ── 4. Waterfall Splits (15/20/50/15) ──────────────────────────────
    reservoir_amount = (distributable_profit * settings.waterfall_reservoir_pct).quantize(PRECISION, rounding=ROUND_HALF_UP)
    nursery_amount = (distributable_profit * settings.waterfall_nursery_pct).quantize(PRECISION, rounding=ROUND_HALF_UP)
    vault_amount = (distributable_profit * settings.waterfall_vault_pct).quantize(PRECISION, rounding=ROUND_HALF_UP)
    reinvestment_amount = (distributable_profit * settings.waterfall_reinvestment_pct).quantize(PRECISION, rounding=ROUND_HALF_UP)

    # Rounding to Vault
    distributed_total = reservoir_amount + nursery_amount + vault_amount + reinvestment_amount
    rounding_remainder = distributable_profit - distributed_total
    vault_amount += rounding_remainder

    # ── 5. Apply Balances ──────────────────────────────────────────────
    
    # 5a. Credit Master (if applicable)
    if master_state and platform_fee > 0:
        await update_balances(session, master_state, reservoir_delta=platform_fee)
        state.total_platform_fees_paid += platform_fee

    # 5b. Route Member Vault
    vault_result = await apply_tiered_vault(session, vault_amount, state)

    # 5c. Update Member Balances
    await update_balances(
        session,
        state,
        reservoir_delta=reservoir_amount,
        nursery_delta=nursery_amount,
        vault_tier2_delta=vault_result.tier2_deposit,
        vault_tier3_delta=vault_result.tier3_deposit,
    )

    # ── 6. Reinvestment & Thresholds ──────────────────────────────────
    if seed_id and reinvestment_amount > 0:
        from app.models.seed import Seed
        seed_stmt = select(Seed).where(Seed.seed_id == seed_id).with_for_update()
        res = await session.execute(seed_stmt)
        seed = res.scalar_one_or_none()
        if seed:
            seed.current_value += reinvestment_amount

    nursery_threshold_reached = state.shared_nursery_balance >= settings.nursery_seed_threshold

    return WaterfallResult(
        gross_profit=gross_profit,
        fees=fees,
        tax_reserve=tax_reserve,
        platform_fee=platform_fee,
        net_profit_after_tax=net_profit_at,
        distributable_profit=distributable_profit,
        reservoir=reservoir_amount,
        nursery=nursery_amount,
        vault_total=vault_amount,
        vault_tier2_deposit=vault_result.tier2_deposit,
        vault_tier3_deposit=vault_result.tier3_deposit,
        reinvestment=reinvestment_amount,
        nursery_threshold_reached=nursery_threshold_reached
    )

def _zero_result(gross: Decimal, fees: Decimal, tax: Decimal, net: Decimal) -> WaterfallResult:
    return WaterfallResult(
        gross_profit=gross, fees=fees, tax_reserve=tax, platform_fee=Decimal("0"),
        net_profit_after_tax=net, distributable_profit=Decimal("0"), reservoir=Decimal("0"),
        nursery=Decimal("0"), vault_total=Decimal("0"), vault_tier2_deposit=Decimal("0"),
        vault_tier3_deposit=Decimal("0"), reinvestment=Decimal("0"), nursery_threshold_reached=False
    )
