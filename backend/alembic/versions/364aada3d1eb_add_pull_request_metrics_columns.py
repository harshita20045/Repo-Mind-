"""add_pull_request_metrics_columns

Revision ID: 364aada3d1eb
Revises: b41c9e8f2a10
Create Date: 2026-11-12 11:13:09.911491

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '364aada3d1eb'
down_revision: Union[str, None] = 'b41c9e8f2a10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Safely add additions, deletions, files_changed if not already present
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('pull_request')]

    if 'additions' not in columns:
        op.add_column('pull_request', sa.Column('additions', sa.Integer(), nullable=True))
    if 'deletions' not in columns:
        op.add_column('pull_request', sa.Column('deletions', sa.Integer(), nullable=True))
    if 'files_changed' not in columns:
        op.add_column('pull_request', sa.Column('files_changed', sa.Integer(), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('pull_request')]

    if 'files_changed' in columns:
        op.drop_column('pull_request', 'files_changed')
    if 'deletions' in columns:
        op.drop_column('pull_request', 'deletions')
    if 'additions' in columns:
        op.drop_column('pull_request', 'additions')
