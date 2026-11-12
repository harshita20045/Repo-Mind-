"""add_claim_token_to_review_run

Revision ID: 5e34700732dc
Revises: f3f9473f10b8
Create Date: 2026-11-12 12:57:57.933568

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5e34700732dc'
down_revision: Union[str, None] = 'f3f9473f10b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('review_run')]

    if 'claim_token' not in columns:
        op.add_column('review_run', sa.Column('claim_token', sa.String(64), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('review_run')]

    if 'claim_token' in columns:
        op.drop_column('review_run', 'claim_token')
