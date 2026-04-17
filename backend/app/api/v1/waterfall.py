"""
Waterfall API endpoints.

POST /api/v1/waterfall/execute — Execute the 15/20/50/15 profit distribution.
GET  /api/v1/state              — Retrieve the current global state snapshot.
"""

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import (
    GlobalStateResponse,
    WaterfallDistribution,
    WaterfallRequest,
    WaterfallResponse,
)
from app.services.state_manager import get_global_state
from app.services.waterfall import execute_waterfall
from app.api.deps import get_current_user
from app.models.user import User
from app.models.tree import Tree
from sqlalchemy import select

router = APIRouter()


@router.post(
    "/waterfall/execute",
    response_model=WaterfallResponse,
    summary="Execute the 4-Way Profit Waterfall",
    description=(
        "Atomically distributes a trade's gross profit across Reservoir (15%), "
        "Nursery (20%), Vault (50%), and Reinvestment (15%) per Master Document §1.1. "
        "The Vault allocation routes through the Tiered Liquidity Ladder (§1.2)."
    ),
)
async def execute_waterfall_endpoint(
    request: WaterfallRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Execute the atomic waterfall distribution."""
    try:
        result = await execute_waterfall(
            session=session,
            user=current_user,
            gross_profit=request.gross_profit,
            fees=request.fees,
            tax_rate=request.tax_rate,
            seed_id=request.seed_id,
        )

        return WaterfallResponse(
            success=True,
            distribution=WaterfallDistribution(
                gross_profit=result.gross_profit,
                fees=result.fees,
                tax_reserve=result.tax_reserve,
                net_profit=result.net_profit_after_tax,
                reservoir=result.reservoir,
                nursery=result.nursery,
                vault_total=result.vault_total,
                vault_tier2_deposit=result.vault_tier2_deposit,
                vault_tier3_deposit=result.vault_tier3_deposit,
                reinvestment=result.reinvestment,
                nursery_threshold_reached=result.nursery_threshold_reached,
            ),
            message="Waterfall distribution executed successfully.",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Session rollback is handled by the get_db dependency
        raise HTTPException(
            status_code=500,
            detail=f"Waterfall execution failed: {str(e)}",
        )


@router.get(
    "/state",
    response_model=GlobalStateResponse,
    summary="Get Global State",
    description="Returns the current snapshot of the Unified Root global state.",
)
async def get_state_endpoint(
    session: AsyncSession = Depends(get_db),
):
    """Retrieve the current global state."""
    from app.services.forex_service import ForexService
    try:
        state = await get_global_state(session)
        
        # Dual currency calculations
        rate = await ForexService.get_usd_to_zar()
        total_usd = (
            state.shared_reservoir_balance + 
            state.shared_nursery_balance + 
            state.vault_tier1_buidl + 
            state.vault_tier2_etfs + 
            state.vault_tier3_real_estate
        )
        
        portfolio = {
            "total_value_usd": total_usd,
            "total_value_zar": (total_usd * rate).quantize(Decimal("1.00")),
            "reservoir_zar": (state.shared_reservoir_balance * rate).quantize(Decimal("1.00")),
            "nursery_zar": (state.shared_nursery_balance * rate).quantize(Decimal("1.00")),
            "vault_zar": ((state.vault_tier1_buidl + state.vault_tier2_etfs + state.vault_tier3_real_estate) * rate).quantize(Decimal("1.00")),
            "reinvestment_zar": Decimal("0.00") # Derived dynamically across trees usually, stubbed for now
        }
        
        resp = GlobalStateResponse.model_validate(state)
        resp.usd_zar_rate = rate
        from app.schemas import DualCurrencyPortfolio
        resp.portfolio = DualCurrencyPortfolio(**portfolio)
        
        trees_res = await session.execute(select(Tree))
        db_trees = trees_res.scalars().all()
        resp.trees = [
            {
                "id": t.id,
                "tree_id": t.tree_id,
                "status": t.status,
                "active_seeds_count": t.active_seeds_count
            }
            for t in db_trees
        ]
        
        return resp
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
