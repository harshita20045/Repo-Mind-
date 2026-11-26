"""add_historical_evolution_and_bug_lessons_tables

Revision ID: rm20_011
Revises: rm20_010
Create Date: 2026-11-26 10:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'rm20_011'
down_revision: Union[str, None] = 'rm20_010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # 1. Enhance architecture_decision_record with 15-attribute structured decision fields
    if 'architecture_decision_record' in existing_tables:
        existing_cols = [c['name'] for c in inspector.get_columns('architecture_decision_record')]
        if 'decision_category' not in existing_cols:
            op.add_column('architecture_decision_record', sa.Column('decision_category', sa.String(length=100), nullable=False, server_default='architecture'))
            op.create_index('ix_adr_decision_category', 'architecture_decision_record', ['decision_category'])
        if 'decision_type' not in existing_cols:
            op.add_column('architecture_decision_record', sa.Column('decision_type', sa.String(length=50), nullable=False, server_default='synthetic_demo'))
        if 'original_problem' not in existing_cols:
            op.add_column('architecture_decision_record', sa.Column('original_problem', sa.Text(), nullable=True))
        if 'business_context' not in existing_cols:
            op.add_column('architecture_decision_record', sa.Column('business_context', sa.Text(), nullable=True))
        if 'technical_context' not in existing_cols:
            op.add_column('architecture_decision_record', sa.Column('technical_context', sa.Text(), nullable=True))
        if 'advantages' not in existing_cols:
            op.add_column('architecture_decision_record', sa.Column('advantages', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
        if 'trade_offs' not in existing_cols:
            op.add_column('architecture_decision_record', sa.Column('trade_offs', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
        if 'related_prs' not in existing_cols:
            op.add_column('architecture_decision_record', sa.Column('related_prs', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
        if 'current_relevance' not in existing_cols:
            op.add_column('architecture_decision_record', sa.Column('current_relevance', sa.String(length=100), nullable=False, server_default='active'))

    # 2. historical_evolution_milestone
    if 'historical_evolution_milestone' not in existing_tables:
        op.create_table(
            'historical_evolution_milestone',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column('repository_id', sa.Integer(), sa.ForeignKey('repository.id', ondelete='CASCADE'), nullable=False),
            sa.Column('milestone_date', sa.DateTime(timezone=True), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('category', sa.String(length=100), nullable=False),  # architecture, api, database, dependency, security, performance
            sa.Column('module_name', sa.String(length=100), nullable=False),  # auth, orders, users, core, etc.
            sa.Column('pr_id', sa.Integer(), sa.ForeignKey('pull_request.id', ondelete='SET NULL'), nullable=True),
            sa.Column('commit_sha', sa.String(length=40), nullable=True),
            sa.Column('previous_approach', sa.Text(), nullable=True),
            sa.Column('current_approach', sa.Text(), nullable=True),
            sa.Column('problem_solved', sa.Text(), nullable=False),
            sa.Column('reason_for_change', sa.Text(), nullable=False),
            sa.Column('business_context', sa.Text(), nullable=True),
            sa.Column('technical_explanation', sa.Text(), nullable=True),
            sa.Column('affected_files', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('affected_modules', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('dependencies_impacted', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('consequences', sa.Text(), nullable=True),
            sa.Column('lessons_learned', sa.Text(), nullable=True),
            sa.Column('is_synthetic_demo', sa.Boolean(), nullable=False, server_default=sa.text('true')),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index('ix_milestone_repository_id', 'historical_evolution_milestone', ['repository_id'])
        op.create_index('ix_milestone_category', 'historical_evolution_milestone', ['category'])
        op.create_index('ix_milestone_module_name', 'historical_evolution_milestone', ['module_name'])
        op.create_index('ix_milestone_date', 'historical_evolution_milestone', ['milestone_date'])

    # 3. historical_bug_lesson
    if 'historical_bug_lesson' not in existing_tables:
        op.create_table(
            'historical_bug_lesson',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column('repository_id', sa.Integer(), sa.ForeignKey('repository.id', ondelete='CASCADE'), nullable=False),
            sa.Column('issue_title', sa.String(length=255), nullable=False),
            sa.Column('issue_category', sa.String(length=100), nullable=False),  # concurrency, validation, security, database, api_contract
            sa.Column('module_name', sa.String(length=100), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('root_cause', sa.Text(), nullable=True),
            sa.Column('related_pr_number', sa.Integer(), nullable=True),
            sa.Column('related_commit_sha', sa.String(length=40), nullable=True),
            sa.Column('files_involved', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('resolution_details', sa.Text(), nullable=False),
            sa.Column('tests_added', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('prevention_recommendations', sa.Text(), nullable=False),
            sa.Column('warning_triggers', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index('ix_bug_lesson_repository_id', 'historical_bug_lesson', ['repository_id'])
        op.create_index('ix_bug_lesson_module_name', 'historical_bug_lesson', ['module_name'])
        op.create_index('ix_bug_lesson_category', 'historical_bug_lesson', ['issue_category'])


def downgrade() -> None:
    op.drop_table('historical_bug_lesson')
    op.drop_table('historical_evolution_milestone')
    op.drop_column('architecture_decision_record', 'current_relevance')
    op.drop_column('architecture_decision_record', 'related_prs')
    op.drop_column('architecture_decision_record', 'trade_offs')
    op.drop_column('architecture_decision_record', 'advantages')
    op.drop_column('architecture_decision_record', 'technical_context')
    op.drop_column('architecture_decision_record', 'business_context')
    op.drop_column('architecture_decision_record', 'original_problem')
    op.drop_column('architecture_decision_record', 'decision_type')
    op.drop_column('architecture_decision_record', 'decision_category')
