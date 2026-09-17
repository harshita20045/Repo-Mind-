"""add_ml_prediction

Revision ID: 5a5ce4894f5c
Revises: rm20_003
Create Date: 2026-09-17 11:36:49.582155

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5a5ce4894f5c'
down_revision: Union[str, None] = 'rm20_003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table('ml_prediction',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('pull_request_id', sa.Integer(), nullable=False),
    sa.Column('predicted_delay_category', sa.String(length=50), nullable=False),
    sa.Column('confidence_score', sa.Float(), nullable=True),
    sa.Column('prediction_model_version', sa.String(length=50), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['pull_request_id'], ['pull_request.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ml_prediction_id'), 'ml_prediction', ['id'], unique=False)
    op.create_index(op.f('ix_ml_prediction_pull_request_id'), 'ml_prediction', ['pull_request_id'], unique=True)



def downgrade() -> None:

    op.drop_index(op.f('ix_ml_prediction_pull_request_id'), table_name='ml_prediction')
    op.drop_index(op.f('ix_ml_prediction_id'), table_name='ml_prediction')
    op.drop_table('ml_prediction')

