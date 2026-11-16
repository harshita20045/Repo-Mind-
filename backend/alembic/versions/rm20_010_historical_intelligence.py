"""add_historical_code_intelligence_tables

Revision ID: rm20_010
Revises: rm20_009
Create Date: 2026-11-16 14:20:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'rm20_010'
down_revision: Union[str, None] = 'rm20_009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # 1. architecture_decision_record
    if 'architecture_decision_record' not in existing_tables:
        op.create_table(
            'architecture_decision_record',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column('repository_id', sa.Integer(), sa.ForeignKey('repository.id', ondelete='CASCADE'), nullable=False),
            sa.Column('adr_number', sa.String(length=50), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('status', sa.String(length=50), nullable=False, server_default='Confirmed'),
            sa.Column('context', sa.Text(), nullable=True),
            sa.Column('decision', sa.Text(), nullable=False),
            sa.Column('options_considered', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('reason', sa.Text(), nullable=True),
            sa.Column('consequences', sa.Text(), nullable=True),
            sa.Column('superseded_alternative', sa.Text(), nullable=True),
            sa.Column('file_source', sa.String(length=1024), nullable=True),
            sa.Column('affected_modules', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint('repository_id', 'adr_number', name='uq_adr_repo_number'),
        )
        op.create_index('ix_adr_repository_id', 'architecture_decision_record', ['repository_id'])
        op.create_index('ix_adr_adr_number', 'architecture_decision_record', ['adr_number'])

    # 2. historical_commit_record
    if 'historical_commit_record' not in existing_tables:
        op.create_table(
            'historical_commit_record',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column('repository_id', sa.Integer(), sa.ForeignKey('repository.id', ondelete='CASCADE'), nullable=False),
            sa.Column('commit_sha', sa.String(length=40), nullable=False),
            sa.Column('author', sa.String(length=255), nullable=True),
            sa.Column('committer', sa.String(length=255), nullable=True),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('committed_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('is_bugfix', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('files_changed', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('linked_issues', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('original_decision_rationale', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint('repository_id', 'commit_sha', name='uq_historical_commit_repo_sha'),
        )
        op.create_index('ix_historical_commit_repository_id', 'historical_commit_record', ['repository_id'])
        op.create_index('ix_historical_commit_commit_sha', 'historical_commit_record', ['commit_sha'])
        op.create_index('ix_historical_commit_committed_at', 'historical_commit_record', ['committed_at'])
        op.create_index('ix_historical_commit_is_bugfix', 'historical_commit_record', ['is_bugfix'])

    # 3. recurring_issue_hotspot
    if 'recurring_issue_hotspot' not in existing_tables:
        op.create_table(
            'recurring_issue_hotspot',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column('repository_id', sa.Integer(), sa.ForeignKey('repository.id', ondelete='CASCADE'), nullable=False),
            sa.Column('file_path', sa.String(length=1024), nullable=False),
            sa.Column('total_commits', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('bugfix_commits_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('recurring_findings_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('hotspot_score', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('severity', sa.String(length=50), nullable=False, server_default='low'),
            sa.Column('recurring_finding_categories', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('historical_references', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('last_bugfix_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint('repository_id', 'file_path', name='uq_hotspot_repo_filepath'),
        )
        op.create_index('ix_hotspot_repository_id', 'recurring_issue_hotspot', ['repository_id'])
        op.create_index('ix_hotspot_file_path', 'recurring_issue_hotspot', ['file_path'])


def downgrade() -> None:
    op.drop_table('recurring_issue_hotspot')
    op.drop_table('historical_commit_record')
    op.drop_table('architecture_decision_record')

