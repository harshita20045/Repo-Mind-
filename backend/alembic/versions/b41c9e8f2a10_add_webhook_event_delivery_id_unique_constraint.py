"""add_webhook_event_delivery_id_unique_constraint

Revision ID: b41c9e8f2a10
Revises: 71a3ba5afa1e
Create Date: 2026-11-12 10:35:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'b41c9e8f2a10'
down_revision: Union[str, None] = '71a3ba5afa1e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # In PostgreSQL, create the explicit UNIQUE constraint if it does not already exist
    # Using raw SQL with IF NOT EXISTS or checking constraint existence
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint 
                WHERE conname = 'uq_webhook_event_github_delivery_id'
            ) THEN
                ALTER TABLE webhook_event 
                ADD CONSTRAINT uq_webhook_event_github_delivery_id 
                UNIQUE (github_delivery_id);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint 
                WHERE conname = 'uq_webhook_event_github_delivery_id'
            ) THEN
                ALTER TABLE webhook_event 
                DROP CONSTRAINT uq_webhook_event_github_delivery_id;
            END IF;
        END $$;
    """)

