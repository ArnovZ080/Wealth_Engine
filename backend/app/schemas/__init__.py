"""
Pydantic schemas for waterfall and state API requests/responses.

All monetary fields use Decimal with explicit validation to prevent
float contamination at the API boundary.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict

# ── Request Schemas ─────────────────────────────────────────────────────


class WaterfallRequest(BaseModel):
    """
    Input for execute_waterfall().

    All values must be non-negative Decimals. The tax_rate can be overridden
    per-invocation; if omitted, the stored default (0.30) is used.
    """

    gross_profit: Decimal = Field(
        ...,
        ge=Decimal("0"),
        description="Gross profit from the closed trade, before fees and tax",
    )
    fees: Decimal = Field(
        ...,
        ge=Decimal("0"),
        description="Total trading fees (exchange + network + slippage)",
    )
    tax_rate: Optional[Decimal] = Field(
        None,
        ge=Decimal("0"),
        le=Decimal("1"),
        description="Tax reserve rate override (0.00–1.00). If None, uses stored default.",
    )
    seed_id: Optional[str] = Field(
        None,
        description="Seed ID for reinvestment routing. If None, reinvestment is pooled.",
    )

    @field_validator("gross_profit", "fees", mode="before")
    @classmethod
    def coerce_to_decimal(cls, v):
        if isinstance(v, float):
            # Convert float to string first to preserve precision
            return Decimal(str(v))
        return v


# ── Response Schemas ────────────────────────────────────────────────────


class WaterfallDistribution(BaseModel):
    """Breakdown of a single waterfall execution."""

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
    nursery_threshold_reached: bool = Field(
        False,
        description="True if nursery balance >= $100 after this distribution",
    )


class WaterfallResponse(BaseModel):
    """API response wrapping a waterfall distribution result."""

    success: bool
    distribution: Optional[WaterfallDistribution] = None
    message: str = ""


class TieredVaultBreakdown(BaseModel):
    """Result of apply_tiered_vault() showing where vault funds were routed."""

    amount_in: Decimal
    tier2_deposit: Decimal
    tier3_deposit: Decimal
    tier2_remaining_capacity: Decimal
    tier2_saturated: bool


class BoostLogEntry(BaseModel):
    """Single boost event in the boost log."""

    type: str = Field(..., pattern="^(expansion|acceleration|fortress)$")
    amount: Decimal
    timestamp: datetime


class DualCurrencyPortfolio(BaseModel):
    """Dual currency breakdown of internal funds."""
    total_value_usd: Decimal
    total_value_zar: Decimal
    reservoir_zar: Decimal
    nursery_zar: Decimal
    vault_zar: Decimal
    reinvestment_zar: Decimal


class GlobalStateResponse(BaseModel):
    """Full global state snapshot for API consumers."""

    id: str
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        return str(v)
        
    shared_reservoir_balance: Decimal
    shared_nursery_balance: Decimal
    vault_tier1_buidl: Decimal
    vault_tier2_etfs: Decimal
    vault_tier2_capacity: Decimal
    vault_tier3_real_estate: Decimal
    last_heartbeat: datetime
    kill_switch_status: str
    strike_count: int
    preflight_passed: bool
    tax_rate: Decimal
    legacy_heir_wallet: Optional[str]
    legacy_trust_contract: Optional[str]
    legacy_triggered: bool
    boost_log: list = []
    trees: list = []
    created_at: datetime
    updated_at: datetime
    
    # --- Phase 5 Dual Currency fields ---
    usd_zar_rate: Optional[Decimal] = None
    portfolio: Optional[DualCurrencyPortfolio] = None

    model_config = ConfigDict(from_attributes=True)


class HeartbeatResponse(BaseModel):
    """Response from heartbeat status check."""

    last_heartbeat: datetime
    days_inactive: int
    status: str = Field(
        ...,
        description="NORMAL | WARNING_90 | WARNING_150 | LEGACY_TRIGGER",
    )
    message: str
    legacy_triggered: bool
