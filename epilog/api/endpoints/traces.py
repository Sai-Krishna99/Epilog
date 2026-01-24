"""Trace ingestion and query endpoints."""

import base64
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from epilog.api.dependencies import get_db
from epilog.api.schemas import (
    TraceEventCreate,
    TraceEventResponse,
    TraceSessionCreate,
    TraceSessionResponse,
)
from epilog.db.models import TraceEvent, TraceSession

router = APIRouter()


@router.post("/sessions", response_model=TraceSessionResponse, status_code=201)
async def create_session(
    session_data: TraceSessionCreate,
    db: AsyncSession = Depends(get_db),
) -> TraceSession:
    """Create a new trace session."""
    new_session = TraceSession(
        name=session_data.name,
        session_metadata=session_data.session_metadata,
    )
    db.add(new_session)
    await db.flush()
    await db.refresh(new_session)
    return new_session


@router.get("/sessions", response_model=List[TraceSessionResponse])
async def list_sessions(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> List[TraceSession]:
    """List trace sessions with pagination."""
    result = await db.execute(
        select(TraceSession)
        .order_by(TraceSession.started_at.desc())
        .offset(skip)
        .limit(limit)
    )
    sessions = result.scalars().all()

    # Add event count to each session
    for session in sessions:
        count_result = await db.execute(
            select(func.count(TraceEvent.id)).where(TraceEvent.session_id == session.id)
        )
        session.event_count = count_result.scalar()

    return list(sessions)


@router.get("/sessions/{session_id}", response_model=TraceSessionResponse)
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> TraceSession:
    """Get a single trace session by ID."""
    result = await db.execute(
        select(TraceSession).where(TraceSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Add event count
    count_result = await db.execute(
        select(func.count(TraceEvent.id)).where(TraceEvent.session_id == session_id)
    )
    session.event_count = count_result.scalar()

    return session


@router.post("/events", response_model=TraceEventResponse, status_code=201)
async def create_event(
    event_data: TraceEventCreate,
    db: AsyncSession = Depends(get_db),
) -> TraceEvent:
    """Ingest a single trace event."""
    # Decode screenshot if provided
    screenshot_bytes = None
    if event_data.screenshot_base64:
        try:
            screenshot_bytes = base64.b64decode(event_data.screenshot_base64)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid base64 screenshot data: {str(e)}"
            )

    new_event = TraceEvent(
        session_id=event_data.session_id,
        run_id=event_data.run_id,
        parent_run_id=event_data.parent_run_id,
        event_type=event_data.event_type,
        timestamp=event_data.timestamp,
        event_data=event_data.event_data,
        screenshot=screenshot_bytes,
    )
    db.add(new_event)
    await db.flush()
    await db.refresh(new_event)

    # Add has_screenshot flag
    new_event.has_screenshot = new_event.screenshot is not None

    return new_event


@router.get("/sessions/{session_id}/events", response_model=List[TraceEventResponse])
async def get_session_events(
    session_id: UUID,
    skip: int = 0,
    limit: int = 1000,
    db: AsyncSession = Depends(get_db),
) -> List[TraceEvent]:
    """Get events for a specific session."""
    result = await db.execute(
        select(TraceEvent)
        .where(TraceEvent.session_id == session_id)
        .order_by(TraceEvent.timestamp.asc())
        .offset(skip)
        .limit(limit)
    )
    events = result.scalars().all()

    # Add has_screenshot flag to each event
    for event in events:
        event.has_screenshot = event.screenshot is not None

    return list(events)


@router.get("/events/{event_id}/screenshot")
async def get_event_screenshot(
    event_id: int,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Get screenshot for a specific event."""
    result = await db.execute(
        select(TraceEvent).where(TraceEvent.id == event_id)
    )
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if not event.screenshot:
        raise HTTPException(status_code=404, detail="Screenshot not found for this event")

    return Response(content=event.screenshot, media_type="image/png")
