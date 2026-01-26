"""SQLAlchemy models for trace storage."""

from datetime import datetime
from enum import Enum as PyEnum
import uuid

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    LargeBinary,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class SessionStatus(str, PyEnum):
    running = "running"
    completed = "completed"
    failed = "failed"


class TraceSession(Base):
    __tablename__ = "trace_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(SessionStatus), nullable=False, default=SessionStatus.running)
    session_metadata = Column("metadata", JSONB, nullable=True)

    events = relationship("TraceEvent", back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_trace_sessions_started_at", "started_at"),
        Index("ix_trace_sessions_status", "status"),
    )
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "status": self.status.value if self.status else None,
            "metadata": self.session_metadata
        }


class TraceEvent(Base):
    __tablename__ = "trace_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("trace_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    run_id = Column(UUID(as_uuid=True), nullable=False)
    parent_run_id = Column(UUID(as_uuid=True), nullable=True)
    event_type = Column(String(50), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    event_data = Column(JSONB, nullable=False)
    screenshot = Column(LargeBinary, nullable=True)

    session = relationship("TraceSession", back_populates="events")

    __table_args__ = (
        Index("ix_trace_events_session_id", "session_id"),
        Index("ix_trace_events_run_id", "run_id"),
        Index("ix_trace_events_event_type", "event_type"),
        Index("ix_trace_events_timestamp", "timestamp"),
        Index("ix_trace_events_event_data", "event_data", postgresql_using="gin"),
    )
    
    def to_dict(self):
        return {
            "id": self.id,
            "session_id": str(self.session_id),
            "run_id": str(self.run_id),
            "parent_run_id": str(self.parent_run_id) if self.parent_run_id else None,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "event_data": self.event_data,
            "has_screenshot": self.screenshot is not None
        }
