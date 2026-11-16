"""add_architecture_intelligence_tables

Revision ID: rm20_006
Revises: rm20_005
Create Date: 2026-11-16 01:36:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'rm20_006'
down_revision: Union[str, None] = 'rm20_005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # 1. architecture_rule
    if 'architecture_rule' not in existing_tables:
        op.create_table(
            'architecture_rule',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('repository_id', sa.Integer(), nullable=False),
            sa.Column('rule_code', sa.String(length=64), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('rule_type', sa.String(length=50), nullable=False),
            sa.Column('source_layer', sa.String(length=100), nullable=True),
            sa.Column('target_layer', sa.String(length=100), nullable=True),
            sa.Column('source_pattern', sa.String(length=255), nullable=True),
            sa.Column('target_pattern', sa.String(length=255), nullable=True),
            sa.Column('severity', sa.String(length=50), nullable=False, server_default='high'),
            sa.Column('suggested_fix', sa.Text(), nullable=True),
            sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('is_system_inferred', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['repository_id'], ['repository.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('repository_id', 'rule_code', name='uq_architecture_rule_repo_code'),
        )
        op.create_index('ix_architecture_rule_id', 'architecture_rule', ['id'])
        op.create_index('ix_architecture_rule_repository_id', 'architecture_rule', ['repository_id'])
        op.create_index('ix_architecture_rule_rule_code', 'architecture_rule', ['rule_code'])
        op.create_index('ix_architecture_rule_is_enabled', 'architecture_rule', ['is_enabled'])

    # 2. architecture_analysis
    if 'architecture_analysis' not in existing_tables:
        op.create_table(
            'architecture_analysis',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('repository_id', sa.Integer(), nullable=False),
            sa.Column('pull_request_id', sa.Integer(), nullable=True),
            sa.Column('health_score', sa.Integer(), nullable=False, server_default='100'),
            sa.Column('inferred_pattern', sa.String(length=100), nullable=False, server_default='layered_mvc'),
            sa.Column('pattern_confidence', sa.Float(), nullable=False, server_default='1.0'),
            sa.Column('total_violations', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('critical_violations', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('circular_dependency_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('layer_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('flow_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('mermaid_diagram', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['repository_id'], ['repository.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['pull_request_id'], ['pull_request.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_architecture_analysis_id', 'architecture_analysis', ['id'])
        op.create_index('ix_architecture_analysis_repository_id', 'architecture_analysis', ['repository_id'])
        op.create_index('ix_architecture_analysis_pull_request_id', 'architecture_analysis', ['pull_request_id'])

    # 3. architecture_violation
    if 'architecture_violation' not in existing_tables:
        op.create_table(
            'architecture_violation',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('analysis_id', sa.Integer(), nullable=False),
            sa.Column('rule_id', sa.Integer(), nullable=True),
            sa.Column('rule_code', sa.String(length=64), nullable=False),
            sa.Column('violation_type', sa.String(length=50), nullable=False),
            sa.Column('severity', sa.String(length=50), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('explanation', sa.Text(), nullable=False),
            sa.Column('suggested_correction', sa.Text(), nullable=False),
            sa.Column('source_file', sa.String(length=1024), nullable=False),
            sa.Column('source_line', sa.Integer(), nullable=True),
            sa.Column('target_file', sa.String(length=1024), nullable=True),
            sa.Column('target_line', sa.Integer(), nullable=True),
            sa.Column('evidence', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['analysis_id'], ['architecture_analysis.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['rule_id'], ['architecture_rule.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_architecture_violation_id', 'architecture_violation', ['id'])
        op.create_index('ix_architecture_violation_analysis_id', 'architecture_violation', ['analysis_id'])
        op.create_index('ix_architecture_violation_rule_code', 'architecture_violation', ['rule_code'])


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'architecture_violation' in existing_tables:
        op.drop_table('architecture_violation')
    if 'architecture_analysis' in existing_tables:
        op.drop_table('architecture_analysis')
    if 'architecture_rule' in existing_tables:
        op.drop_table('architecture_rule')
