"""add_test_intelligence_tables

Revision ID: rm20_007
Revises: rm20_006
Create Date: 2026-11-16 11:25:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'rm20_007'
down_revision: Union[str, None] = 'rm20_006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # 1. test_scenario table
    if 'test_scenario' not in existing_tables:
        op.create_table(
            'test_scenario',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('repository_id', sa.Integer(), nullable=False),
            sa.Column('pull_request_id', sa.Integer(), nullable=True),
            sa.Column('review_run_id', sa.Integer(), nullable=True),
            sa.Column('target_file', sa.String(length=1024), nullable=False),
            sa.Column('target_symbol', sa.String(length=255), nullable=False),
            sa.Column('category', sa.String(length=50), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('edge_case_notes', sa.Text(), nullable=True),
            sa.Column('suggested_assertions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('existing_test_file', sa.String(length=1024), nullable=True),
            sa.Column('coverage_gap', sa.Boolean(), server_default='true', nullable=False),
            sa.Column('impacted_endpoints', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('impacted_services', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('priority', sa.String(length=20), server_default='medium', nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['repository_id'], ['repository.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['pull_request_id'], ['pull_request.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['review_run_id'], ['review_run.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_test_scenario_repository_id'), 'test_scenario', ['repository_id'], unique=False)
        op.create_index(op.f('ix_test_scenario_pull_request_id'), 'test_scenario', ['pull_request_id'], unique=False)
        op.create_index(op.f('ix_test_scenario_review_run_id'), 'test_scenario', ['review_run_id'], unique=False)
        op.create_index(op.f('ix_test_scenario_target_file'), 'test_scenario', ['target_file'], unique=False)
        op.create_index(op.f('ix_test_scenario_target_symbol'), 'test_scenario', ['target_symbol'], unique=False)
        op.create_index(op.f('ix_test_scenario_category'), 'test_scenario', ['category'], unique=False)

    # 2. generated_test_case table
    if 'generated_test_case' not in existing_tables:
        op.create_table(
            'generated_test_case',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('test_scenario_id', sa.Integer(), nullable=False),
            sa.Column('language', sa.String(length=50), nullable=False),
            sa.Column('framework', sa.String(length=50), nullable=False),
            sa.Column('test_file_path', sa.String(length=1024), nullable=False),
            sa.Column('test_code', sa.Text(), nullable=False),
            sa.Column('execution_status', sa.String(length=50), server_default='pending', nullable=False),
            sa.Column('execution_result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('security_reviewed', sa.Boolean(), server_default='false', nullable=False),
            sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['test_scenario_id'], ['test_scenario.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_generated_test_case_test_scenario_id'), 'generated_test_case', ['test_scenario_id'], unique=False)
        op.create_index(op.f('ix_generated_test_case_execution_status'), 'generated_test_case', ['execution_status'], unique=False)


def downgrade() -> None:
    op.drop_table('generated_test_case')
    op.drop_table('test_scenario')

