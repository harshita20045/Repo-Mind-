"""Add lifecycle_status to finding"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'rm20_003'
down_revision: Union[str, None] = 'rm20_002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('finding', sa.Column('lifecycle_status', sa.String(length=50), nullable=True, server_default='new'))

def downgrade() -> None:
    op.drop_column('finding', 'lifecycle_status')
