"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class TraceSessionCreate(BaseModel):
    name: Optional[str] = None
    session_metadata: Optional[dict] = Field(default=None, alias="metadata")

    model_config = {
        "populate_by_name": True,
    }


class TraceSessionResponse(BaseModel):
    id: UUID
    name: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]
    status: str
    event_count: Optional[int] = None

    model_config = {
        "from_attributes": True,
    }


class TraceEventCreate(BaseModel):
    session_id: UUID
    run_id: UUID
    parent_run_id: Optional[UUID] = None
    event_type: str = Field(..., max_length=50)
    timestamp: datetime
    event_data: dict
    screenshot_base64: Optional[str] = None

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("event_type cannot be empty")
        return v.strip()


class TraceEventResponse(BaseModel):
    id: int
    session_id: UUID
    run_id: UUID
    parent_run_id: Optional[UUID]
    event_type: str
    timestamp: datetime
    has_screenshot: bool

    model_config = {
        "from_attributes": True,
    }
