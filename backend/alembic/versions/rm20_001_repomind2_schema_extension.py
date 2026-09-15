"""RepoMind 2.0 schema extension — roles, new tables, column additions

Revision ID: rm20_001
Revises: a1b2c3d4e5f6
Create Date: 2026-09-16

Changes:
  1. organization_membership.role — add new role enum values
     (org_owner, eng_manager, tech_lead, security_reviewer, read_only)
  2. review_run — add intelligence_mode, progress_message, error_message columns
  3. finding — add evidence_status, lifecycle_status columns
  4. risk_assessment — new table (PR-level risk score)
  5. conflict — new table (semantic + mechanical conflicts)
  6. finding_evidence — new table (grounded evidence per finding)
  7. human_decision — new table (human approval/rejection audit)
  8. chat_session — new table
  9. chat_message — new table
  10. webhook_event — new table

downgrade() reverses all changes in reverse dependency order.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = 'rm20_001'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # 1. Update organization_membership.role column to accept new values.
    #    The column is VARCHAR (native_enum=False), so no ALTER TYPE needed.
    #    New role strings are simply valid values now.
    #    No SQL change needed — the enum validation is in Python, not the DB.
    # -------------------------------------------------------------------------
    # (No DDL required for VARCHAR role column — new values accepted automatically)

    # -------------------------------------------------------------------------
    # 2. review_run — add new columns
    # -------------------------------------------------------------------------
    op.add_column('review_run', sa.Column(
        'intelligence_mode', sa.String(length=20), nullable=True, server_default='v1'
    ))
    op.add_column('review_run', sa.Column(
        'progress_message', sa.String(length=255), nullable=True
    ))
    op.add_column('review_run', sa.Column(
        'error_message', sa.Text(), nullable=True
    ))

    # -------------------------------------------------------------------------
    # 3. finding — add evidence_status, lifecycle_status
    # -------------------------------------------------------------------------
    op.add_column('finding', sa.Column(
        'evidence_status', sa.String(length=50), nullable=True, server_default='unverified'
    ))
    op.add_column('finding', sa.Column(
        'lifecycle_status', sa.String(length=50), nullable=True, server_default='new'
    ))

    # -------------------------------------------------------------------------
    # 4. risk_assessment
    # -------------------------------------------------------------------------
    op.create_table(
        'risk_assessment',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('review_run_id', sa.Integer(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('level', sa.String(length=20), nullable=False, server_default='low'),
        sa.Column('factors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('blast_radius', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('test_impact', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('calculated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['review_run_id'], ['review_run.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('review_run_id', name='uq_risk_assessment_review_run'),
    )
    op.create_index('ix_risk_assessment_id', 'risk_assessment', ['id'], unique=False)
    op.create_index('ix_risk_assessment_review_run_id', 'risk_assessment', ['review_run_id'], unique=False)

    # -------------------------------------------------------------------------
    # 5. conflict
    # -------------------------------------------------------------------------
    op.create_table(
        'conflict',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('review_run_id', sa.Integer(), nullable=False),
        sa.Column('conflict_type', sa.String(length=50), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('severity', sa.String(length=50), nullable=False, server_default='medium'),
        sa.Column('title', sa.String(length=512), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('evidence', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='open'),
        sa.ForeignKeyConstraint(['review_run_id'], ['review_run.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_conflict_id', 'conflict', ['id'], unique=False)
    op.create_index('ix_conflict_review_run_id', 'conflict', ['review_run_id'], unique=False)

    # -------------------------------------------------------------------------
    # 6. finding_evidence
    # -------------------------------------------------------------------------
    op.create_table(
        'finding_evidence',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('finding_id', sa.Integer(), nullable=False),
        sa.Column('evidence_status', sa.String(length=50), nullable=False, server_default='unverified'),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('source_path', sa.String(length=1024), nullable=True),
        sa.Column('source_text', sa.Text(), nullable=True),
        sa.Column('citation_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['finding_id'], ['finding.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_finding_evidence_id', 'finding_evidence', ['id'], unique=False)
    op.create_index('ix_finding_evidence_finding_id', 'finding_evidence', ['finding_id'], unique=False)

    # -------------------------------------------------------------------------
    # 7. human_decision
    # -------------------------------------------------------------------------
    op.create_table(
        'human_decision',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('review_run_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('target_type', sa.String(length=50), nullable=True),
        sa.Column('target_id', sa.Integer(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['review_run_id'], ['review_run.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_human_decision_id', 'human_decision', ['id'], unique=False)
    op.create_index('ix_human_decision_review_run_id', 'human_decision', ['review_run_id'], unique=False)
    op.create_index('ix_human_decision_user_id', 'human_decision', ['user_id'], unique=False)

    # -------------------------------------------------------------------------
    # 8. chat_session
    # -------------------------------------------------------------------------
    op.create_table(
        'chat_session',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('context_type', sa.String(length=50), nullable=False),
        sa.Column('context_id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_chat_session_id', 'chat_session', ['id'], unique=False)
    op.create_index('ix_chat_session_user_id', 'chat_session', ['user_id'], unique=False)
    op.create_index('ix_chat_session_organization_id', 'chat_session', ['organization_id'], unique=False)

    # -------------------------------------------------------------------------
    # 9. chat_message
    # -------------------------------------------------------------------------
    op.create_table(
        'chat_message',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('sources', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_grounded', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['chat_session.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_chat_message_id', 'chat_message', ['id'], unique=False)
    op.create_index('ix_chat_message_session_id', 'chat_message', ['session_id'], unique=False)

    # -------------------------------------------------------------------------
    # 10. webhook_event
    # -------------------------------------------------------------------------
    op.create_table(
        'webhook_event',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('github_delivery_id', sa.String(length=255), nullable=True),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=True),
        sa.Column('repository_id', sa.Integer(), nullable=True),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='received'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['repository_id'], ['repository.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_webhook_event_id', 'webhook_event', ['id'], unique=False)
    op.create_index('ix_webhook_event_github_delivery_id', 'webhook_event', ['github_delivery_id'], unique=True)
    op.create_index('ix_webhook_event_repository_id', 'webhook_event', ['repository_id'], unique=False)
    op.create_index('ix_webhook_event_received_at', 'webhook_event', ['received_at'], unique=False)


def downgrade() -> None:
    # Drop in reverse dependency order

    # webhook_event
    op.drop_index('ix_webhook_event_received_at', table_name='webhook_event')
    op.drop_index('ix_webhook_event_repository_id', table_name='webhook_event')
    op.drop_index('ix_webhook_event_github_delivery_id', table_name='webhook_event')
    op.drop_index('ix_webhook_event_id', table_name='webhook_event')
    op.drop_table('webhook_event')

    # chat_message
    op.drop_index('ix_chat_message_session_id', table_name='chat_message')
    op.drop_index('ix_chat_message_id', table_name='chat_message')
    op.drop_table('chat_message')

    # chat_session
    op.drop_index('ix_chat_session_organization_id', table_name='chat_session')
    op.drop_index('ix_chat_session_user_id', table_name='chat_session')
    op.drop_index('ix_chat_session_id', table_name='chat_session')
    op.drop_table('chat_session')

    # human_decision
    op.drop_index('ix_human_decision_user_id', table_name='human_decision')
    op.drop_index('ix_human_decision_review_run_id', table_name='human_decision')
    op.drop_index('ix_human_decision_id', table_name='human_decision')
    op.drop_table('human_decision')

    # finding_evidence
    op.drop_index('ix_finding_evidence_finding_id', table_name='finding_evidence')
    op.drop_index('ix_finding_evidence_id', table_name='finding_evidence')
    op.drop_table('finding_evidence')

    # conflict
    op.drop_index('ix_conflict_review_run_id', table_name='conflict')
    op.drop_index('ix_conflict_id', table_name='conflict')
    op.drop_table('conflict')

    # risk_assessment
    op.drop_index('ix_risk_assessment_review_run_id', table_name='risk_assessment')
    op.drop_index('ix_risk_assessment_id', table_name='risk_assessment')
    op.drop_table('risk_assessment')

    # finding columns
    op.drop_column('finding', 'lifecycle_status')
    op.drop_column('finding', 'evidence_status')

    # review_run columns
    op.drop_column('review_run', 'error_message')
    op.drop_column('review_run', 'progress_message')
    op.drop_column('review_run', 'intelligence_mode')
