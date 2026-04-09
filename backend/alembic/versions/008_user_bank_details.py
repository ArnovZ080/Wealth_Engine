"""Add bank details and deposit reference to users

Fields for tracking EFT deposits and providing unique references.
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "008_user_bank_details"
down_revision: Union[str, None] = "007_funding_transactions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column("users", sa.Column("deposit_reference", sa.String(20), nullable=True, unique=True))
    op.add_column("users", sa.Column("bank_name", sa.String(100), nullable=True))
    op.add_column("users", sa.Column("bank_account_number", sa.String(50), nullable=True))
    op.add_column("users", sa.Column("bank_branch_code", sa.String(20), nullable=True))

def downgrade() -> None:
    op.drop_column("users", "bank_branch_code")
    op.drop_column("users", "bank_account_number")
    op.drop_column("users", "bank_name")
    op.drop_column("users", "deposit_reference")
