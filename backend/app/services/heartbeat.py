"""
Heartbeat Service — User Activity Monitoring & Legacy Protocol.

Implements Master Document §11.1 (Heartbeat System) and §11.2 (Legacy Protocol).

The Heartbeat is the user's proof-of-life signal. If it lapses, the system
escalates through warning stages and ultimately triggers the Legacy Protocol
(Dead Man's Switch) at 180 days of inactivity.

Phase 1 Scope:
  - Heartbeat timestamp update
  - Inactivity detection with tiered warnings (90 / 150 / 180 days)
  - Legacy Protocol trigger stub (sets flag + global_pause)
  - Actual asset transfer is deferred to Phase 5 (Security Architecture)
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.services.state_manager import get_global_state

logger = logging.getLogger(__name__)
settings = get_settings()


# ── Inactivity Status Codes ─────────────────────────────────────────────

NORMAL = "NORMAL"
WARNING_90 = "WARNING_90"
WARNING_150 = "WARNING_150"
LEGACY_TRIGGER = "LEGACY_TRIGGER"


_STATUS_MESSAGES = {
    NORMAL: "System operational. Heartbeat is current.",
    WARNING_90: (
        "⚠️ 90-day inactivity warning. Please log in to confirm continued operation. "
        "Legacy Protocol will trigger at 180 days."
    ),
    WARNING_150: (
        "⚠️⚠️ 150-day inactivity warning. System entering conservative mode. "
        "New seed planting is reduced. Legacy Protocol triggers in 30 days."
    ),
    LEGACY_TRIGGER: (
        "🔒 180-day inactivity threshold breached. Legacy Protocol activated. "
        "System is now in Global Pause. All assets flagged for heir transfer."
    ),
}


@dataclass(frozen=True)
class InactivityStatus:
    """Result of an inactivity check."""

    last_heartbeat: datetime
    days_inactive: int
    status: str
    message: str
    legacy_triggered: bool


async def update_heartbeat(session: AsyncSession) -> datetime:
    """
    Record a heartbeat — proof-of-life from the user.

    Updates the last_heartbeat timestamp to NOW() and resets
    the kill_switch_status if it was in a legacy-triggered pause.

    Master Document §11.1: "System records user login activity as a Heartbeat timestamp."

    Args:
        session: Active async session.

    Returns:
        The new heartbeat timestamp.
    """
    state = await get_global_state(session, for_update=True)

    now = datetime.now(timezone.utc)
    state.last_heartbeat = now

    # If the user logs back in after a Legacy trigger, reset the pause.
    # The actual asset transfer (Phase 5) would need a separate undo mechanism,
    # but for Phase 1, resetting the flag is sufficient.
    if state.legacy_triggered:
        logger.warning(
            "User heartbeat received after Legacy Protocol was triggered. "
            "Resetting legacy_triggered flag and restoring active status."
        )
        state.legacy_triggered = False
        state.kill_switch_status = "active"

    logger.info("Heartbeat updated: %s", now.isoformat())
    return now


async def check_inactivity(session: AsyncSession) -> InactivityStatus:
    """
    Check the current inactivity level against the heartbeat thresholds.

    Master Document §11.1 Escalation Ladder:
      - 0–89 days:   NORMAL
      - 90–149 days:  WARNING_90 — notification dispatched
      - 150–179 days: WARNING_150 — conservative mode, reduced seed planting
      - 180+ days:    LEGACY_TRIGGER — Dead Man's Switch fires

    Args:
        session: Active async session.

    Returns:
        InactivityStatus with days inactive, status code, and message.
    """
    state = await get_global_state(session, for_update=True)

    now = datetime.now(timezone.utc)
    last_hb = state.last_heartbeat

    # Ensure timezone-aware comparison
    if last_hb.tzinfo is None:
        last_hb = last_hb.replace(tzinfo=timezone.utc)

    delta = now - last_hb
    days_inactive = delta.days

    if days_inactive >= settings.heartbeat_legacy_trigger_days:
        # ── 180+ days: Legacy Protocol ─────────────────────────────────
        status = LEGACY_TRIGGER
        if not state.legacy_triggered:
            await _trigger_legacy_protocol(state)
    elif days_inactive >= settings.heartbeat_warning_days_2:
        # ── 150–179 days: Conservative Mode ────────────────────────────
        status = WARNING_150
    elif days_inactive >= settings.heartbeat_warning_days_1:
        # ── 90–149 days: First Warning ─────────────────────────────────
        status = WARNING_90
    else:
        # ── 0–89 days: Normal ──────────────────────────────────────────
        status = NORMAL

    logger.info(
        "Inactivity check: %d days since last heartbeat → %s",
        days_inactive,
        status,
    )

    return InactivityStatus(
        last_heartbeat=last_hb,
        days_inactive=days_inactive,
        status=status,
        message=_STATUS_MESSAGES[status],
        legacy_triggered=state.legacy_triggered,
    )


async def _trigger_legacy_protocol(state) -> None:
    """
    Execute the Legacy Protocol (Dead Man's Switch).

    Master Document §11.2:
      "If current_time − last_heartbeat > 180 days → execute_legacy_protocol()."

    Phase 1 Implementation (Stub):
      - Sets legacy_triggered = True
      - Sets kill_switch_status = 'global_pause'
      - Logs the trigger event

    Phase 5 will implement the actual Hierarchical Transfer Sequence:
      1. Reservoir (BUIDL) → Heir Wallet
      2. Nursery Vault (USDC) → Heir Wallet
      3. Vault Tier 2 (ETFs) → Family Trust Smart Contract
      4. Vault Tier 3 (Real Estate tokens) → Family Trust Smart Contract
      5. Active Seeds → Graceful wind-down, proceeds swept to Heir Wallet

    Args:
        state: GlobalState instance (must have FOR UPDATE lock).
    """
    state.legacy_triggered = True
    state.kill_switch_status = "global_pause"

    logger.critical(
        "🔒 LEGACY PROTOCOL TRIGGERED — 180-day inactivity threshold breached. "
        "System entering Global Pause. Heir wallet: %s, Trust contract: %s",
        state.legacy_heir_wallet or "(not configured)",
        state.legacy_trust_contract or "(not configured)",
    )

    # Phase 5: Execute the Hierarchical Transfer Sequence here.
    # For now, the trigger is recorded and the system is paused.
    # The actual asset transfer requires EIP-7702 Smart Wallet integration.
