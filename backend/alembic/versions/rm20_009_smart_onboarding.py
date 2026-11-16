"""add_smart_onboarding_columns

Revision ID: rm20_009
Revises: rm20_008
Create Date: 2026-11-16 12:35:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'rm20_009'
down_revision: Union[str, None] = 'rm20_008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('repository_blueprint')]

    if 'application_flows' not in columns:
        op.add_column(
            'repository_blueprint',
            sa.Column('application_flows', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
        )

    if 'lifecycle_diagram' not in columns:
        op.add_column(
            'repository_blueprint',
            sa.Column('lifecycle_diagram', sa.Text(), nullable=True)
        )

    if 'glossary' not in columns:
        op.add_column(
            'repository_blueprint',
            sa.Column('glossary', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
        )


def downgrade() -> None:
    op.drop_column('repository_blueprint', 'glossary')
    op.drop_column('repository_blueprint', 'lifecycle_diagram')
    op.drop_column('repository_blueprint', 'application_flows')

