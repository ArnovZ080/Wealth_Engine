"""Add dumb_mode_agreed flag to trade_decisions

Allows tracking performance compared to technical baseline.
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "005_add_dumb_mode_flag"
down_revision: Union[str, None] = "004_exchange_credentials"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column(
        "trade_decisions",
        sa.Column("dumb_mode_agreed", sa.Boolean(), nullable=False, server_default="TRUE")
    )

def downgrade() -> None:
    op.drop_column("trade_decisions", "dumb_mode_agreed")
