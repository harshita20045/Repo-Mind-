"""RepoMind 2.0 RAG schema extension — 768 dimensions and chunk metadata

Revision ID: rm20_002
Revises: rm20_001
Create Date: 2026-09-16

Changes:
  1. Alter document_chunk.embedding type from vector(384) to vector(768)
  2. Add document_chunk.chunk_type
  3. Add document_chunk.file_path
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers
revision: str = 'rm20_002'
down_revision: Union[str, None] = 'rm20_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Alter vector dimension
    # Changing vector dimensions in Postgres requires a cast or recreating the column.
    # Since we don't have production data yet, altering the type directly with a USING clause or dropping/adding is easiest.
    # For safety in this test setup, we will just use raw SQL to alter the type.
    op.execute("ALTER TABLE document_chunk ALTER COLUMN embedding TYPE vector(768) USING embedding::vector(768)")

    # 2. Add new columns
    op.add_column('document_chunk', sa.Column(
        'chunk_type', sa.String(length=50), nullable=False, server_default='documentation'
    ))
    op.add_column('document_chunk', sa.Column(
        'file_path', sa.String(length=1024), nullable=True
    ))

    # 3. Create indexes
    op.create_index('ix_document_chunk_chunk_type', 'document_chunk', ['chunk_type'], unique=False)
    op.create_index('ix_document_chunk_file_path', 'document_chunk', ['file_path'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_document_chunk_file_path', table_name='document_chunk')
    op.drop_index('ix_document_chunk_chunk_type', table_name='document_chunk')
    op.drop_column('document_chunk', 'file_path')
    op.drop_column('document_chunk', 'chunk_type')
    op.execute("ALTER TABLE document_chunk ALTER COLUMN embedding TYPE vector(384) USING embedding::vector(384)")
