"""add_change_impact_analysis_table

Revision ID: rm20_005
Revises: rm20_004
Create Date: 2026-11-16 01:05:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'rm20_005'
down_revision: Union[str, None] = 'rm20_004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'change_impact_analysis' not in existing_tables:
        op.create_table(
            'change_impact_analysis',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('repository_id', sa.Integer(), nullable=False),
            sa.Column('pull_request_id', sa.Integer(), nullable=True),
            sa.Column('review_run_id', sa.Integer(), nullable=True),
            sa.Column('commit_sha', sa.String(length=255), nullable=True),
            sa.Column('target_branch', sa.String(length=255), nullable=True),
            sa.Column('risk_level', sa.String(length=50), nullable=False, server_default='low'),
            sa.Column('directly_affected_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('indirectly_affected_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('breaking_changes_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('affected_components', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('breaking_changes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('test_recommendations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('graph_visualization', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('summary', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['repository_id'], ['repository.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['pull_request_id'], ['pull_request.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['review_run_id'], ['review_run.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_change_impact_analysis_id', 'change_impact_analysis', ['id'])
        op.create_index('ix_change_impact_analysis_repository_id', 'change_impact_analysis', ['repository_id'])
        op.create_index('ix_change_impact_analysis_pull_request_id', 'change_impact_analysis', ['pull_request_id'])
        op.create_index('ix_change_impact_analysis_review_run_id', 'change_impact_analysis', ['review_run_id'])
        op.create_index('ix_impact_repo_pr', 'change_impact_analysis', ['repository_id', 'pull_request_id'])


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'change_impact_analysis' in existing_tables:
        op.drop_table('change_impact_analysis')
