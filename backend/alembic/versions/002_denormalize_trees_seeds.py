"""Denormalize trees/seeds: relational tables

Migrates from JSONB 'trees' column on global_state to separate relational
tables: 'trees', 'seeds', and 'trade_decisions'.

Revision ID: 002_denormalize_trees_seeds
Revises: 001_initial_schema
Create Date: 2026-04-09
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision: str = "002_denormalize_trees_seeds"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # ── Create 'trees' table ────────────────────────────────────────────
    op.create_table(
        "trees",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tree_id", sa.String(50), unique=True, nullable=False),
        sa.Column("global_state_id", UUID(as_uuid=True), sa.ForeignKey("global_state.id"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'paused'")),
        sa.Column("active_seeds_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("max_seeds", sa.Integer, nullable=False, server_default=sa.text("100")),
        sa.Column("preflight_passed", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    # ── Create 'seeds' table ────────────────────────────────────────────
    op.create_table(
        "seeds",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("seed_id", sa.String(50), unique=True, nullable=False),
        sa.Column("tree_id", UUID(as_uuid=True), sa.ForeignKey("trees.id"), nullable=False),
        sa.Column("current_value", sa.Numeric(20, 8), nullable=False, server_default=sa.text("100.0")),
        sa.Column("initial_value", sa.Numeric(20, 8), nullable=False, server_default=sa.text("100.0")),
        sa.Column("stage", sa.Integer, nullable=False, server_default=sa.text("1")),
        sa.Column("strategy", sa.String(30), nullable=False, server_default=sa.text("'momentum'")),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'active'")),
        sa.Column("roi_30d", sa.Numeric(10, 6), nullable=False, server_default=sa.text("0.0")),
        sa.Column("stop_loss_floor", sa.Numeric(20, 8), nullable=False, server_default=sa.text("85.0")),
        sa.Column("strike_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("boost_applied", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
        sa.Column("confidence_score", sa.Numeric(5, 2), nullable=False, server_default=sa.text("0.0")),
        sa.Column("last_trade_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("performance_metrics", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    # ── Create 'trade_decisions' table ──────────────────────────────────
    op.create_table(
        "trade_decisions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("seed_id", UUID(as_uuid=True), sa.ForeignKey("seeds.id"), nullable=False),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("direction", sa.String(10), nullable=False),
        sa.Column("entry_price", sa.Numeric(20, 8), nullable=False),
        sa.Column("target_exit", sa.Numeric(20, 8), nullable=False),
        sa.Column("stop_loss", sa.Numeric(20, 8), nullable=False),
        sa.Column("position_size", sa.Numeric(20, 8), nullable=False),
        sa.Column("confidence_score", sa.Integer, nullable=False),
        sa.Column("hunter_rationale", sa.Text, nullable=False),
        sa.Column("shadow_verdict", sa.String(20), nullable=False),
        sa.Column("shadow_flaws", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("refinement_rounds", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("execution_authorized", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
        sa.Column("executed", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
        sa.Column("trade_memo", JSONB, nullable=False),
        sa.Column("adversarial_log", JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    # ── Update 'global_state' ───────────────────────────────────────────
    op.add_column("global_state", sa.Column("total_active_seeds", sa.Integer(), nullable=False, server_default=sa.text("0")))
    op.drop_column("global_state", "trees")

def downgrade() -> None:
    op.add_column("global_state", sa.Column("trees", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")))
    op.drop_column("global_state", "total_active_seeds")
    op.drop_table("trade_decisions")
    op.drop_table("seeds")
    op.drop_table("trees")
