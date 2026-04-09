"""
Heartbeat and Legacy Protocol test suite.

Covers:
  1. Heartbeat update — timestamp is current
  2. 90-day warning
  3. 150-day warning
  4. 180-day Legacy Protocol trigger — global_pause set
  5. Heartbeat reset after Legacy trigger
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
import pytest_asyncio

from app.services.heartbeat import (
    LEGACY_TRIGGER,
    NORMAL,
    WARNING_90,
    WARNING_150,
    check_inactivity,
    update_heartbeat,
)
from app.services.state_manager import get_global_state


# ═══════════════════════════════════════════════════════════════════════
# Test 1: Heartbeat Update
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_heartbeat_update(session):
    """
    When: A heartbeat is recorded.
    Then: The last_heartbeat timestamp is within a few seconds of now.
    """
    before = datetime.now(timezone.utc)
    timestamp = await update_heartbeat(session)
    after = datetime.now(timezone.utc)

    assert before <= timestamp <= after

    # Verify DB reflects the update
    state = await get_global_state(session)
    hb = state.last_heartbeat
    if hb.tzinfo is None:
        hb = hb.replace(tzinfo=timezone.utc)
    assert before <= hb <= after


# ═══════════════════════════════════════════════════════════════════════
# Test 2: 90-Day Warning
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_90_day_warning(session):
    """
    Given: Last heartbeat was 91 days ago.
    Expected: Status = WARNING_90.
    """
    state = await get_global_state(session, for_update=True)
    state.last_heartbeat = datetime.now(timezone.utc) - timedelta(days=91)

    await session.flush()

    status = await check_inactivity(session)

    assert status.status == WARNING_90
    assert status.days_inactive >= 91
    assert "90-day" in status.message
    assert status.legacy_triggered is False


# ═══════════════════════════════════════════════════════════════════════
# Test 3: 150-Day Warning
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_150_day_warning(session):
    """
    Given: Last heartbeat was 151 days ago.
    Expected: Status = WARNING_150, conservative mode.
    """
    state = await get_global_state(session, for_update=True)
    state.last_heartbeat = datetime.now(timezone.utc) - timedelta(days=151)

    await session.flush()

    status = await check_inactivity(session)

    assert status.status == WARNING_150
    assert status.days_inactive >= 151
    assert "150-day" in status.message or "conservative" in status.message.lower()
    assert status.legacy_triggered is False


# ═══════════════════════════════════════════════════════════════════════
# Test 4: 180-Day Legacy Protocol Trigger
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_180_day_legacy_trigger(session):
    """
    Given: Last heartbeat was 181 days ago.
    Expected:
      - Status = LEGACY_TRIGGER
      - legacy_triggered = True
      - kill_switch_status = 'global_pause'
    """
    state = await get_global_state(session, for_update=True)
    state.last_heartbeat = datetime.now(timezone.utc) - timedelta(days=181)
    state.legacy_heir_wallet = "0x1234567890abcdef"
    state.legacy_trust_contract = "0xabcdef1234567890"

    await session.flush()

    status = await check_inactivity(session)

    assert status.status == LEGACY_TRIGGER
    assert status.days_inactive >= 181
    assert status.legacy_triggered is True

    # Verify DB state
    db_state = await get_global_state(session)
    assert db_state.legacy_triggered is True
    assert db_state.kill_switch_status == "global_pause"


# ═══════════════════════════════════════════════════════════════════════
# Test 5: Heartbeat Reset After Legacy Trigger
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_heartbeat_reset_after_legacy(session):
    """
    Given: Legacy Protocol has been triggered (180+ days inactive).
    When: User sends a new heartbeat.
    Expected: legacy_triggered reset to False, status back to 'active'.
    """
    # Trigger the Legacy Protocol
    state = await get_global_state(session, for_update=True)
    state.last_heartbeat = datetime.now(timezone.utc) - timedelta(days=181)

    await session.flush()

    await check_inactivity(session)

    # Verify Legacy was triggered
    pre_state = await get_global_state(session)
    assert pre_state.legacy_triggered is True
    assert pre_state.kill_switch_status == "global_pause"

    # User comes back — sends heartbeat
    await update_heartbeat(session)

    # Verify reset
    post_state = await get_global_state(session)
    assert post_state.legacy_triggered is False
    assert post_state.kill_switch_status == "active"


# ═══════════════════════════════════════════════════════════════════════
# Test 6: Normal Inactivity (< 90 days)
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_normal_inactivity(session):
    """
    Given: Last heartbeat was 10 days ago.
    Expected: Status = NORMAL.
    """
    state = await get_global_state(session, for_update=True)
    state.last_heartbeat = datetime.now(timezone.utc) - timedelta(days=10)

    await session.flush()

    status = await check_inactivity(session)

    assert status.status == NORMAL
    assert status.days_inactive >= 10
    assert status.legacy_triggered is False
