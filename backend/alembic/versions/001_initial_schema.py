"""Initial schema: Global State — Unified Root

Creates the global_state table with full JSONB support for the
Recursive Fractal Wealth Engine.

Schema maps directly to Master Document v3.0 §9.2:
  - Shared balances (Reservoir, Nursery)
  - Tiered Vault (Tier 1 BUIDL, Tier 2 ETFs, Tier 3 Real Estate)
  - Heartbeat & Legacy Protocol fields
  - Kill Switch status & Strike Count
  - Preflight gate
  - Boost Log (JSONB array)
  - Trees/Seeds hierarchy (JSONB)
  - Configurable tax rate & Tier 2 capacity

All monetary columns use NUMERIC(20,8) to enforce Decimal precision
and prevent floating-point arithmetic errors.

Revision ID: 001_initial_schema
Revises: None
Create Date: 2026-04-07
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Create the global_state table ───────────────────────────────────
    op.create_table(
        "global_state",
        # ── Primary Key ─────────────────────────────────────────────────
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            comment="Single-row global state identifier",
        ),
        # ── Shared Balances ─────────────────────────────────────────────
        sa.Column(
            "shared_reservoir_balance",
            sa.Numeric(20, 8),
            nullable=False,
            server_default=sa.text("0"),
            comment="Tier 1 — BlackRock BUIDL / T-Bills instant-access spending wallet",
        ),
        sa.Column(
            "shared_nursery_balance",
            sa.Numeric(20, 8),
            nullable=False,
            server_default=sa.text("0"),
            comment="USDC stablecoin pool — funds all new $100 seeds",
        ),
        # ── Tiered Vault ────────────────────────────────────────────────
        sa.Column(
            "vault_tier1_buidl",
            sa.Numeric(20, 8),
            nullable=False,
            server_default=sa.text("0"),
            comment="Vault Tier 1 — BlackRock BUIDL / T-Bills (Reservoir backing)",
        ),
        sa.Column(
            "vault_tier2_etfs",
            sa.Numeric(20, 8),
            nullable=False,
            server_default=sa.text("0"),
            comment="Vault Tier 2 — Low-cost Index ETFs (VOO / QQQ)",
        ),
        sa.Column(
            "vault_tier2_capacity",
            sa.Numeric(20, 8),
            nullable=False,
            server_default=sa.text("50000"),
            comment="Tier 2 saturation cap — overflow routes to Tier 3 after this amount",
        ),
        sa.Column(
            "vault_tier3_real_estate",
            sa.Numeric(20, 8),
            nullable=False,
            server_default=sa.text("0"),
            comment="Vault Tier 3 — Tokenized Real Estate (RealT / Centrifuge)",
        ),
        # ── Heartbeat & Legacy Protocol ─────────────────────────────────
        sa.Column(
            "last_heartbeat",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="User activity heartbeat — triggers Legacy Protocol at 180 days inactive",
        ),
        sa.Column(
            "legacy_heir_wallet",
            sa.String(256),
            nullable=True,
            comment="Pre-designated heir wallet address for Legacy Protocol transfer",
        ),
        sa.Column(
            "legacy_trust_contract",
            sa.String(256),
            nullable=True,
            comment="Family Trust Smart Contract address for Tier 2/3 assets",
        ),
        sa.Column(
            "legacy_triggered",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("FALSE"),
            comment="Whether the Legacy Protocol (Dead Man's Switch) has been activated",
        ),
        # ── Kill Switch & Monitoring ────────────────────────────────────
        sa.Column(
            "kill_switch_status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'active'"),
            comment="Engine status: active | paused | global_pause",
        ),
        sa.Column(
            "strike_count",
            sa.Integer,
            nullable=False,
            server_default=sa.text("0"),
            comment="Fleet-wide consecutive underperformance counter (0-3, triggers Global Pause at 3)",
        ),
        sa.Column(
            "preflight_passed",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("FALSE"),
            comment="Whether current configuration has passed Pre-Flight Simulation",
        ),
        # ── Tax Rate ───────────────────────────────────────────────────
        sa.Column(
            "tax_rate",
            sa.Numeric(5, 4),
            nullable=False,
            server_default=sa.text("0.3000"),
            comment="Default tax reserve rate applied during waterfall distribution",
        ),
        # ── JSONB Fields ────────────────────────────────────────────────
        sa.Column(
            "boost_log",
            JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
            comment="Array of boost events: [{type, amount, timestamp}]",
        ),
        sa.Column(
            "trees",
            JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
            comment="Full tree/seed hierarchy per Master Document §9.2",
        ),
        # ── Timestamps ──────────────────────────────────────────────────
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="Row creation timestamp",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="Last modification timestamp",
        ),
    )

    # ── Indexes ─────────────────────────────────────────────────────────
    op.create_index(
        "ix_global_state_last_heartbeat",
        "global_state",
        ["last_heartbeat"],
    )
    op.create_index(
        "ix_global_state_kill_switch",
        "global_state",
        ["kill_switch_status"],
    )

    # ── Seed the initial global state row ───────────────────────────────
    # The engine operates on a single-row pattern. This row is created once
    # and updated atomically by all waterfall and state operations.
    op.execute(
        sa.text(
            """
            INSERT INTO global_state (
                id,
                shared_reservoir_balance,
                shared_nursery_balance,
                vault_tier1_buidl,
                vault_tier2_etfs,
                vault_tier2_capacity,
                vault_tier3_real_estate,
                last_heartbeat,
                legacy_triggered,
                kill_switch_status,
                strike_count,
                preflight_passed,
                tax_rate,
                boost_log,
                trees,
                created_at,
                updated_at
            ) VALUES (
                gen_random_uuid(),
                0.00000000,
                0.00000000,
                0.00000000,
                0.00000000,
                50000.00000000,
                0.00000000,
                NOW(),
                FALSE,
                'active',
                0,
                FALSE,
                0.3000,
                '[]'::jsonb,
                '[]'::jsonb,
                NOW(),
                NOW()
            )
            """
        )
    )


def downgrade() -> None:
    op.drop_index("ix_global_state_kill_switch", table_name="global_state")
    op.drop_index("ix_global_state_last_heartbeat", table_name="global_state")
    op.drop_table("global_state")
