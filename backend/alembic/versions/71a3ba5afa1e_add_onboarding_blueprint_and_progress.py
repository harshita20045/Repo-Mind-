"""add_onboarding_blueprint_and_progress

Revision ID: 71a3ba5afa1e
Revises: 2426528e6df4
Create Date: 2026-11-11 14:09:56.691606

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '71a3ba5afa1e'
down_revision: Union[str, None] = '2426528e6df4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create repository_blueprint table
    op.create_table(
        'repository_blueprint',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('repository_id', sa.Integer(), nullable=False),
        sa.Column('analyzed_commit_sha', sa.String(length=40), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('generation_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('generation_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('generation_error', sa.Text(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('architecture_pattern', sa.String(length=100), nullable=True),
        sa.Column('subsystems', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('request_flow', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('tracks', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('caution_zones', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('safe_starter_areas', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('mermaid_diagram', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['repository_id'], ['repository.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_repository_blueprint_analyzed_commit_sha'), 'repository_blueprint', ['analyzed_commit_sha'], unique=False)
    op.create_index(op.f('ix_repository_blueprint_id'), 'repository_blueprint', ['id'], unique=False)
    op.create_index(op.f('ix_repository_blueprint_repository_id'), 'repository_blueprint', ['repository_id'], unique=True)
    op.create_index(op.f('ix_repository_blueprint_status'), 'repository_blueprint', ['status'], unique=False)

    # 2. Create user_onboarding_progress table
    op.create_table(
        'user_onboarding_progress',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('repository_id', sa.Integer(), nullable=False),
        sa.Column('active_track', sa.String(length=50), nullable=False, server_default='backend'),
        sa.Column('completed_milestones', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['repository_id'], ['repository.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'repository_id', name='uq_user_repo_onboarding')
    )
    op.create_index(op.f('ix_user_onboarding_progress_id'), 'user_onboarding_progress', ['id'], unique=False)
    op.create_index(op.f('ix_user_onboarding_progress_repository_id'), 'user_onboarding_progress', ['repository_id'], unique=False)
    op.create_index(op.f('ix_user_onboarding_progress_user_id'), 'user_onboarding_progress', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_onboarding_progress_user_id'), table_name='user_onboarding_progress')
    op.drop_index(op.f('ix_user_onboarding_progress_repository_id'), table_name='user_onboarding_progress')
    op.drop_index(op.f('ix_user_onboarding_progress_id'), table_name='user_onboarding_progress')
    op.drop_table('user_onboarding_progress')

    op.drop_index(op.f('ix_repository_blueprint_status'), table_name='repository_blueprint')
    op.drop_index(op.f('ix_repository_blueprint_repository_id'), table_name='repository_blueprint')
    op.drop_index(op.f('ix_repository_blueprint_id'), table_name='repository_blueprint')
    op.drop_index(op.f('ix_repository_blueprint_analyzed_commit_sha'), table_name='repository_blueprint')
    op.drop_table('repository_blueprint')
