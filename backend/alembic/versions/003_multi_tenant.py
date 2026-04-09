"""Multi-tenant infrastructure

Creates users, invite_codes, and user_forest_state tables.
Migrates trees to be user-scoped.
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "003_multi_tenant"
down_revision: Union[str, None] = "002_denormalize_trees_seeds"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # ── Create 'users' table ────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="member"),
        sa.Column("invited_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("platform_fee_rate", sa.Numeric(5, 4), nullable=False, server_default="0.0500"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="TRUE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("last_heartbeat", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    # ── Create 'invite_codes' table ──────────────────────────────────────
    op.create_table(
        "invite_codes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(20), unique=True, nullable=False),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("claimed_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── Create 'user_forest_state' table ──────────────────────────────────
    op.create_table(
        "user_forest_state",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), unique=True, nullable=False),
        sa.Column("shared_reservoir_balance", sa.Numeric(20, 8), nullable=False, server_default="0.0"),
        sa.Column("shared_nursery_balance", sa.Numeric(20, 8), nullable=False, server_default="0.0"),
        sa.Column("vault_tier1_buidl", sa.Numeric(20, 8), nullable=False, server_default="0.0"),
        sa.Column("vault_tier2_etfs", sa.Numeric(20, 8), nullable=False, server_default="0.0"),
        sa.Column("vault_tier3_realestate", sa.Numeric(20, 8), nullable=False, server_default="0.0"),
        sa.Column("kill_switch_status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("total_platform_fees_paid", sa.Numeric(20, 8), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    # ── Update 'trees' to include user_id ───────────────────────────────
    # We make it nullable first to allow existing records, then backfill, then non-nullable.
    op.add_column("trees", sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True))

    # Optional: Backfill logic could go here once a user is created.
    # For now, we'll keep it nullable or expect the user to run a seeding script.
    
    # We also loosen global_state_id on trees as it's being deprecated.
    op.alter_column("trees", "global_state_id", existing_type=UUID, nullable=True)

def downgrade() -> None:
    op.drop_column("trees", "user_id")
    op.drop_table("user_forest_state")
    op.drop_table("invite_codes")
    op.drop_table("users")
