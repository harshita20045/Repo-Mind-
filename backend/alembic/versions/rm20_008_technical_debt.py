"""add_technical_debt_tables

Revision ID: rm20_008
Revises: rm20_007
Create Date: 2026-11-16 12:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'rm20_008'
down_revision: Union[str, None] = 'rm20_007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # 1. technical_debt_snapshot table
    if 'technical_debt_snapshot' not in existing_tables:
        op.create_table(
            'technical_debt_snapshot',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('repository_id', sa.Integer(), nullable=False),
            sa.Column('commit_sha', sa.String(length=40), nullable=True),
            sa.Column('branch', sa.String(length=255), server_default='main', nullable=False),
            sa.Column('health_score', sa.Integer(), server_default='100', nullable=False),
            sa.Column('total_issues', sa.Integer(), server_default='0', nullable=False),
            sa.Column('critical_issues', sa.Integer(), server_default='0', nullable=False),
            sa.Column('high_issues', sa.Integer(), server_default='0', nullable=False),
            sa.Column('medium_issues', sa.Integer(), server_default='0', nullable=False),
            sa.Column('low_issues', sa.Integer(), server_default='0', nullable=False),
            sa.Column('total_debt_hours', sa.Float(), server_default='0.0', nullable=False),
            sa.Column('category_breakdown', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('most_affected_modules', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('scanned_files_count', sa.Integer(), server_default='0', nullable=False),
            sa.Column('scanned_lines_count', sa.Integer(), server_default='0', nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['repository_id'], ['repository.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_technical_debt_snapshot_repository_id'), 'technical_debt_snapshot', ['repository_id'], unique=False)

    # 2. technical_debt_issue table
    if 'technical_debt_issue' not in existing_tables:
        op.create_table(
            'technical_debt_issue',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('repository_id', sa.Integer(), nullable=False),
            sa.Column('snapshot_id', sa.Integer(), nullable=True),
            sa.Column('category', sa.String(length=50), nullable=False),
            sa.Column('severity', sa.String(length=20), server_default='medium', nullable=False),
            sa.Column('status', sa.String(length=20), server_default='open', nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('explanation', sa.Text(), nullable=False),
            sa.Column('file_path', sa.String(length=1024), nullable=False),
            sa.Column('line_start', sa.Integer(), nullable=True),
            sa.Column('line_end', sa.Integer(), nullable=True),
            sa.Column('symbol_name', sa.String(length=255), nullable=True),
            sa.Column('evidence', sa.Text(), nullable=True),
            sa.Column('recommended_action', sa.Text(), nullable=False),
            sa.Column('estimated_remediation_hours', sa.Float(), server_default='1.0', nullable=False),
            sa.Column('resolution_notes', sa.Text(), nullable=True),
            sa.Column('resolved_by_user_id', sa.Integer(), nullable=True),
            sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('fingerprint', sa.String(length=64), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['repository_id'], ['repository.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['snapshot_id'], ['technical_debt_snapshot.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['resolved_by_user_id'], ['user.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_technical_debt_issue_repository_id'), 'technical_debt_issue', ['repository_id'], unique=False)
        op.create_index(op.f('ix_technical_debt_issue_snapshot_id'), 'technical_debt_issue', ['snapshot_id'], unique=False)
        op.create_index(op.f('ix_technical_debt_issue_category'), 'technical_debt_issue', ['category'], unique=False)
        op.create_index(op.f('ix_technical_debt_issue_severity'), 'technical_debt_issue', ['severity'], unique=False)
        op.create_index(op.f('ix_technical_debt_issue_status'), 'technical_debt_issue', ['status'], unique=False)
        op.create_index(op.f('ix_technical_debt_issue_fingerprint'), 'technical_debt_issue', ['fingerprint'], unique=False)


def downgrade() -> None:
    op.drop_table('technical_debt_issue')
    op.drop_table('technical_debt_snapshot')

