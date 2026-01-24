"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-01-24 15:48:36.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum type for session status
    op.execute("CREATE TYPE sessionstatus AS ENUM ('running', 'completed', 'failed')")

    # Create trace_sessions table
    op.create_table(
        'trace_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', postgresql.ENUM('running', 'completed', 'failed', name='sessionstatus'), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for trace_sessions
    op.create_index('ix_trace_sessions_started_at', 'trace_sessions', ['started_at'], unique=False)
    op.create_index('ix_trace_sessions_status', 'trace_sessions', ['status'], unique=False)

    # Create trace_events table
    op.create_table(
        'trace_events',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parent_run_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('event_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('screenshot', sa.LargeBinary(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['trace_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for trace_events
    op.create_index('ix_trace_events_session_id', 'trace_events', ['session_id'], unique=False)
    op.create_index('ix_trace_events_run_id', 'trace_events', ['run_id'], unique=False)
    op.create_index('ix_trace_events_event_type', 'trace_events', ['event_type'], unique=False)
    op.create_index('ix_trace_events_timestamp', 'trace_events', ['timestamp'], unique=False)
    op.create_index('ix_trace_events_event_data', 'trace_events', ['event_data'], unique=False, postgresql_using='gin')

    # Set TOAST storage to EXTERNAL for screenshot column
    op.execute("ALTER TABLE trace_events ALTER COLUMN screenshot SET STORAGE EXTERNAL")


def downgrade() -> None:
    # Drop tables
    op.drop_index('ix_trace_events_event_data', table_name='trace_events')
    op.drop_index('ix_trace_events_timestamp', table_name='trace_events')
    op.drop_index('ix_trace_events_event_type', table_name='trace_events')
    op.drop_index('ix_trace_events_run_id', table_name='trace_events')
    op.drop_index('ix_trace_events_session_id', table_name='trace_events')
    op.drop_table('trace_events')

    op.drop_index('ix_trace_sessions_status', table_name='trace_sessions')
    op.drop_index('ix_trace_sessions_started_at', table_name='trace_sessions')
    op.drop_table('trace_sessions')

    # Drop enum type
    op.execute("DROP TYPE sessionstatus")
