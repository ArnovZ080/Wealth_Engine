"""Create funding_transactions table

Table for tracking ZAR deposits, hierarchical withdrawals, and exchange conversions.
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "007_funding_transactions"
down_revision: Union[str, None] = "006_position_monitor_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "funding_transactions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("amount_zar", sa.Numeric(20, 2), nullable=False),
        sa.Column("exchange_rate", sa.Numeric(20, 8), nullable=True),
        sa.Column("exchange_amount", sa.Numeric(20, 8), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("reference_code", sa.String(20), nullable=False),
        sa.Column("bank_reference", sa.String(100), nullable=True),
        sa.Column("manual_review_flag", sa.Boolean(), nullable=False, server_default="FALSE"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

def downgrade() -> None:
    op.drop_table("funding_transactions")
