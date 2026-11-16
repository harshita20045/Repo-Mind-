"""update_embedding_to_384

Revision ID: 9ebe0b6eb803
Revises: 5a5ce4894f5c
Create Date: 2026-09-17 14:51:54.044788

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9ebe0b6eb803'
down_revision: Union[str, None] = '5a5ce4894f5c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    has_vector = bind.execute(sa.text("SELECT 1 FROM pg_available_extensions WHERE name = 'vector'")).scalar()
    if has_vector:
        op.execute("ALTER TABLE document_chunk ALTER COLUMN embedding TYPE vector(384);")


def downgrade() -> None:
    op.execute("ALTER TABLE document_chunk ALTER COLUMN embedding TYPE vector(1536);")
