"""add_code_knowledge_graph_and_intelligence_models

Revision ID: rm20_004
Revises: 5e34700732dc
Create Date: 2026-11-16 00:05:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'rm20_004'
down_revision: Union[str, None] = '5e34700732dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # 1. code_graph_node
    if 'code_graph_node' not in existing_tables:
        op.create_table(
            'code_graph_node',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('repository_id', sa.Integer(), nullable=False),
            sa.Column('node_key', sa.String(length=512), nullable=False),
            sa.Column('node_type', sa.String(length=50), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('file_path', sa.String(length=1024), nullable=False),
            sa.Column('start_line', sa.Integer(), nullable=True),
            sa.Column('end_line', sa.Integer(), nullable=True),
            sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['repository_id'], ['repository.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('repository_id', 'node_key', name='uq_code_graph_node_repo_key')
        )
        op.create_index(op.f('ix_code_graph_node_id'), 'code_graph_node', ['id'], unique=False)
        op.create_index(op.f('ix_code_graph_node_repository_id'), 'code_graph_node', ['repository_id'], unique=False)
        op.create_index(op.f('ix_code_graph_node_node_key'), 'code_graph_node', ['node_key'], unique=False)
        op.create_index(op.f('ix_code_graph_node_node_type'), 'code_graph_node', ['node_type'], unique=False)
        op.create_index(op.f('ix_code_graph_node_name'), 'code_graph_node', ['name'], unique=False)
        op.create_index(op.f('ix_code_graph_node_file_path'), 'code_graph_node', ['file_path'], unique=False)

    # 2. code_graph_edge
    if 'code_graph_edge' not in existing_tables:
        op.create_table(
            'code_graph_edge',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('repository_id', sa.Integer(), nullable=False),
            sa.Column('source_node_id', sa.Integer(), nullable=False),
            sa.Column('target_node_id', sa.Integer(), nullable=False),
            sa.Column('relation_type', sa.String(length=50), nullable=False),
            sa.Column('weight', sa.Float(), nullable=False, server_default='1.0'),
            sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.ForeignKeyConstraint(['repository_id'], ['repository.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['source_node_id'], ['code_graph_node.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['target_node_id'], ['code_graph_node.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_code_graph_edge_id'), 'code_graph_edge', ['id'], unique=False)
        op.create_index(op.f('ix_code_graph_edge_repository_id'), 'code_graph_edge', ['repository_id'], unique=False)
        op.create_index(op.f('ix_code_graph_edge_source_node_id'), 'code_graph_edge', ['source_node_id'], unique=False)
        op.create_index(op.f('ix_code_graph_edge_target_node_id'), 'code_graph_edge', ['target_node_id'], unique=False)
        op.create_index(op.f('ix_code_graph_edge_relation_type'), 'code_graph_edge', ['relation_type'], unique=False)

    # 3. package_dependency
    if 'package_dependency' not in existing_tables:
        op.create_table(
            'package_dependency',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('repository_id', sa.Integer(), nullable=False),
            sa.Column('ecosystem', sa.String(length=50), nullable=False),
            sa.Column('package_name', sa.String(length=255), nullable=False),
            sa.Column('version_spec', sa.String(length=100), nullable=True),
            sa.Column('is_dev', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('file_path', sa.String(length=1024), nullable=True),
            sa.ForeignKeyConstraint(['repository_id'], ['repository.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_package_dependency_id'), 'package_dependency', ['id'], unique=False)
        op.create_index(op.f('ix_package_dependency_repository_id'), 'package_dependency', ['repository_id'], unique=False)
        op.create_index(op.f('ix_package_dependency_ecosystem'), 'package_dependency', ['ecosystem'], unique=False)
        op.create_index(op.f('ix_package_dependency_package_name'), 'package_dependency', ['package_name'], unique=False)

    # 4. repository_scan_summary
    if 'repository_scan_summary' not in existing_tables:
        op.create_table(
            'repository_scan_summary',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('repository_id', sa.Integer(), nullable=False),
            sa.Column('primary_language', sa.String(length=50), nullable=True),
            sa.Column('languages', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('frameworks', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('entry_points', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('stats', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('architecture_summary', sa.Text(), nullable=True),
            sa.Column('mermaid_diagram', sa.Text(), nullable=True),
            sa.Column('scanned_commit_sha', sa.String(length=40), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['repository_id'], ['repository.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('repository_id', name='uq_repository_scan_summary_repo')
        )
        op.create_index(op.f('ix_repository_scan_summary_id'), 'repository_scan_summary', ['id'], unique=False)
        op.create_index(op.f('ix_repository_scan_summary_repository_id'), 'repository_scan_summary', ['repository_id'], unique=True)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'repository_scan_summary' in existing_tables:
        op.drop_table('repository_scan_summary')
    if 'package_dependency' in existing_tables:
        op.drop_table('package_dependency')
    if 'code_graph_edge' in existing_tables:
        op.drop_table('code_graph_edge')
    if 'code_graph_node' in existing_tables:
        op.drop_table('code_graph_node')
