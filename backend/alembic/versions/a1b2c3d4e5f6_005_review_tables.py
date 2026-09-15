"""review_run finding linter_result — Phase 8 migration

Revision ID: a1b2c3d4e5f6
Revises: f2a7b8f58af8
Create Date: 2026-09-14

Adds three tables per Docs/03-design/database-design.md Migration 005:
  - review_run
  - finding
  - linter_result

NOTE: linter_result table is created here per the documented migration plan.
      Actual linter execution logic is Phase 9 and is NOT included here.

downgrade() reverses the schema change cleanly. All tables are dropped
in reverse dependency order (finding and linter_result before review_run).
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'f2a7b8f58af8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- review_run -----------------------------------------------------------
    op.create_table(
        'review_run',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column(
            'pull_request_id', sa.Integer(), nullable=False,
            comment='FK to pull_request.id; CASCADE on delete.'
        ),
        sa.Column('commit_sha', sa.String(length=255), nullable=True),
        # status: pending | running | completed | failed | cancelled
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('repomind_version', sa.String(length=50), nullable=True),
        sa.Column('prompt_version', sa.String(length=50), nullable=True),
        sa.Column('llm_model', sa.String(length=255), nullable=True),
        sa.Column('rag_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ['pull_request_id'], ['pull_request.id'],
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_review_run_id'), 'review_run', ['id'], unique=False)
    op.create_index(
        op.f('ix_review_run_pull_request_id'),
        'review_run', ['pull_request_id'], unique=False,
    )

    # --- finding --------------------------------------------------------------
    op.create_table(
        'finding',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('review_run_id', sa.Integer(), nullable=False),
        # type (category): standards_violation | style | security | performance | general
        sa.Column('type', sa.String(length=100), nullable=False),
        # severity: critical | high | medium | low | info
        sa.Column('severity', sa.String(length=50), nullable=False),
        sa.Column('file', sa.String(length=1024), nullable=True),
        sa.Column('line', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=512), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('rule_source', sa.Text(), nullable=True),
        sa.Column('recommendation', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False),
        # status: open | accepted | rejected | resolved
        sa.Column('status', sa.String(length=50), nullable=False, server_default='open'),
        sa.ForeignKeyConstraint(
            ['review_run_id'], ['review_run.id'],
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_finding_id'), 'finding', ['id'], unique=False)
    op.create_index(
        op.f('ix_finding_review_run_id'),
        'finding', ['review_run_id'], unique=False,
    )

    # --- linter_result --------------------------------------------------------
    # Table created now (Phase 8); linter execution logic is Phase 9.
    op.create_table(
        'linter_result',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('review_run_id', sa.Integer(), nullable=False),
        sa.Column('tool', sa.String(length=255), nullable=False),
        sa.Column('raw_output', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(
            ['review_run_id'], ['review_run.id'],
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_linter_result_id'), 'linter_result', ['id'], unique=False)
    op.create_index(
        op.f('ix_linter_result_review_run_id'),
        'linter_result', ['review_run_id'], unique=False,
    )


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_index(op.f('ix_linter_result_review_run_id'), table_name='linter_result')
    op.drop_index(op.f('ix_linter_result_id'), table_name='linter_result')
    op.drop_table('linter_result')

    op.drop_index(op.f('ix_finding_review_run_id'), table_name='finding')
    op.drop_index(op.f('ix_finding_id'), table_name='finding')
    op.drop_table('finding')

    op.drop_index(op.f('ix_review_run_pull_request_id'), table_name='review_run')
    op.drop_index(op.f('ix_review_run_id'), table_name='review_run')
    op.drop_table('review_run')
