"""003_pull_request_and_commit

Phase 5 — GitHub Integration.
Adds pull_request and commit tables per database-design.md (migration 003).

Revision ID: f52225de5db9
Revises: 09cc8a4080e0
Create Date: 2026-09-08 15:25:44

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f52225de5db9'
down_revision: Union[str, None] = '09cc8a4080e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'pull_request',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('repository_id', sa.Integer(), nullable=False),
        sa.Column('github_number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=512), nullable=False),
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('state', sa.String(length=50), nullable=False, server_default='open'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('merged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('additions', sa.Integer(), nullable=True),
        sa.Column('deletions', sa.Integer(), nullable=True),
        sa.Column('files_changed', sa.Integer(), nullable=True),
        sa.Column('head_sha', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['repository_id'], ['repository.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('repository_id', 'github_number', name='uq_pull_request_repo_number'),
    )
    op.create_index(op.f('ix_pull_request_id'), 'pull_request', ['id'], unique=False)
    op.create_index(op.f('ix_pull_request_repository_id'), 'pull_request', ['repository_id'], unique=False)

    op.create_table(
        'commit',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('pull_request_id', sa.Integer(), nullable=False),
        sa.Column('sha', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['pull_request_id'], ['pull_request.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_commit_id'), 'commit', ['id'], unique=False)
    op.create_index(op.f('ix_commit_pull_request_id'), 'commit', ['pull_request_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_commit_pull_request_id'), table_name='commit')
    op.drop_index(op.f('ix_commit_id'), table_name='commit')
    op.drop_table('commit')
    op.drop_index(op.f('ix_pull_request_repository_id'), table_name='pull_request')
    op.drop_index(op.f('ix_pull_request_id'), table_name='pull_request')
    op.drop_table('pull_request')
