"""add_missing_webhook_event_columns

Revision ID: db0ec7da784d
Revises: a29d00a3e5e1
Create Date: 2026-09-29 15:38:40.436634

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db0ec7da784d'
down_revision: Union[str, None] = 'a29d00a3e5e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add missing columns to webhook_event that exist in the model but not the DB
    op.add_column('webhook_event', sa.Column('action', sa.String(100), nullable=True))
    op.add_column('webhook_event', sa.Column('status', sa.String(50), nullable=True, server_default='received'))
    op.add_column('webhook_event', sa.Column('error_message', sa.Text(), nullable=True))
    op.add_column('webhook_event', sa.Column('received_at', sa.DateTime(timezone=True), nullable=True))

    # Backfill: set status='received' where null, received_at from created_at
    op.execute("UPDATE webhook_event SET status = 'received' WHERE status IS NULL")
    op.execute("UPDATE webhook_event SET received_at = created_at WHERE received_at IS NULL")


def downgrade() -> None:
    op.drop_column('webhook_event', 'received_at')
    op.drop_column('webhook_event', 'error_message')
    op.drop_column('webhook_event', 'status')
    op.drop_column('webhook_event', 'action')
