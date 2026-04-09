"""
Tests for Multi-Tenant Waterfall with Platform Fees.
"""

import pytest
from decimal import Decimal
from sqlalchemy import select
from app.models.user import User, UserRole
from app.models.forest import UserForestState
from app.services.waterfall import execute_waterfall
from app.config import get_settings

settings = get_settings()

@pytest.mark.asyncio
async def test_waterfall_member_fee_to_master(db_session):
    """
    Verify that a member's trade results in a 5% platform fee flow to the Master's reservoir.
    """
    # 1. Setup Master User
    master = User(
        email="master@test.com",
        display_name="Master",
        hashed_password="...",
        role=UserRole.MASTER,
        platform_fee_rate=Decimal("0.0")
    )
    master_forest = UserForestState(user_id=master.id)
    db_session.add(master)
    db_session.add(master_forest)
    
    # 2. Setup Member User
    member = User(
        email="member@test.com",
        display_name="Member",
        hashed_password="...",
        role=UserRole.MEMBER,
        platform_fee_rate=Decimal("0.05") # 5% fee
    )
    member_forest = UserForestState(user_id=member.id)
    db_session.add(member)
    db_session.add(member_forest)
    await db_session.flush()

    # 3. Simulate Profit: $100 Gross, $0 Fees, 30% Tax
    # Net Profit After Tax = $70
    # Platform Fee = 5% of $70 = $3.50
    # Distributable = $66.50
    gross = Decimal("100.0")
    fees = Decimal("0.0")
    result = await execute_waterfall(db_session, member, gross, fees)

    # 4. Assertions
    assert result.platform_fee == Decimal("3.50000000")
    assert result.distributable_profit == Decimal("66.50000000")
    
    # Check Master Balance (Fee should be in Reservoir)
    await db_session.refresh(master_forest)
    assert master_forest.shared_reservoir_balance == Decimal("3.50000001") # + initial 1e-8
    
    # Check Member balances (Waterfall split of $66.50)
    await db_session.refresh(member_forest)
    # 15% of 66.50 = 9.975
    assert member_forest.shared_reservoir_balance == Decimal("9.97500001")

@pytest.mark.asyncio
async def test_waterfall_master_zero_fee(db_session):
    """
    Verify that the Master doesn't pay fees to themselves.
    """
    master = User(
        email="master_only@test.com",
        display_name="Master",
        hashed_password="...",
        role=UserRole.MASTER,
        platform_fee_rate=Decimal("0.0")
    )
    forest = UserForestState(user_id=master.id)
    db_session.add(master)
    db_session.add(forest)
    await db_session.flush()

    result = await execute_waterfall(db_session, master, Decimal("100.0"), Decimal("0.0"))
    
    assert result.platform_fee == Decimal("0")
    assert result.net_profit_after_tax == Decimal("70.0") # 30% tax default
    assert result.distributable_profit == Decimal("70.0")
