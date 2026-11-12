"""add_review_run_lease_and_retry_columns

Revision ID: f3f9473f10b8
Revises: 364aada3d1eb
Create Date: 2026-11-12 11:46:55.903672

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3f9473f10b8'
down_revision: Union[str, None] = '364aada3d1eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('review_run')]

    if 'heartbeat_at' not in columns:
        op.add_column('review_run', sa.Column('heartbeat_at', sa.DateTime(timezone=True), nullable=True))
    if 'retry_count' not in columns:
        op.add_column('review_run', sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('review_run')]

    if 'retry_count' in columns:
        op.drop_column('review_run', 'retry_count')
    if 'heartbeat_at' in columns:
        op.drop_column('review_run', 'heartbeat_at')
