"""Add telegram_chat_id to users and bank_transaction_id to funding_transactions

Fields for production hardening:
1. telegram_chat_id (Optional) for notifications.
2. bank_transaction_id (Unique) for deposit detection idempotency.
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "009_prod_hardening"
down_revision: Union[str, None] = "008_user_bank_details"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column("users", sa.Column("telegram_chat_id", sa.String(50), nullable=True))
    op.add_column("funding_transactions", sa.Column("bank_transaction_id", sa.String(100), nullable=True, unique=True))

def downgrade() -> None:
    op.drop_column("funding_transactions", "bank_transaction_id")
    op.drop_column("users", "telegram_chat_id")
