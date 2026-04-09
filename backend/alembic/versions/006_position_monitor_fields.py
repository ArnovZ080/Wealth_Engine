"""Add position monitor fields to trade_decisions

Fields for tracking open/closed status, exit details, and trailing stops.
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "006_position_monitor_fields"
down_revision: Union[str, None] = "005_add_dumb_mode_flag"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column("trade_decisions", sa.Column("status", sa.String(20), nullable=False, server_default="open"))
    op.add_column("trade_decisions", sa.Column("exit_price", sa.Numeric(20, 8), nullable=True))
    op.add_column("trade_decisions", sa.Column("exit_timestamp", sa.DateTime(timezone=True), nullable=True))
    op.add_column("trade_decisions", sa.Column("exit_reason", sa.String(30), nullable=True))
    op.add_column("trade_decisions", sa.Column("highest_price_since_entry", sa.Numeric(20, 8), nullable=True))
    op.add_column("trade_decisions", sa.Column("realized_pnl", sa.Numeric(20, 8), nullable=True))
    op.add_column("trade_decisions", sa.Column("trailing_stop_active", sa.Boolean(), nullable=False, server_default="FALSE"))

def downgrade() -> None:
    op.drop_column("trade_decisions", "trailing_stop_active")
    op.drop_column("trade_decisions", "realized_pnl")
    op.drop_column("trade_decisions", "highest_price_since_entry")
    op.drop_column("trade_decisions", "exit_reason")
    op.drop_column("trade_decisions", "exit_timestamp")
    op.drop_column("trade_decisions", "exit_price")
    op.drop_column("trade_decisions", "status")
