"""Exchange credentials table

Creates table for encrypted API key storage.
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "004_exchange_credentials"
down_revision: Union[str, None] = "003_multi_tenant"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "exchange_credentials",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("exchange", sa.String(50), nullable=False),
        sa.Column("api_key_encrypted", sa.String(512), nullable=False),
        sa.Column("api_secret_encrypted", sa.String(512), nullable=False),
        sa.Column("additional_config", sa.JSON(), nullable=True),
        sa.Column("is_paper_trading", sa.Boolean(), nullable=False, server_default="TRUE"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="TRUE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("user_id", "exchange", name="uq_user_exchange")
    )

def downgrade() -> None:
    op.drop_table("exchange_credentials")
