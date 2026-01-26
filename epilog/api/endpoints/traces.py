"""Trace ingestion and query endpoints."""

import asyncio
import base64
import json
from datetime import datetime
from typing import AsyncGenerator, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from epilog.api.dependencies import get_db
from epilog.db.session import settings
import os
from epilog.api.schemas import (
    TraceEventCreate,
    TraceEventResponse,
    TraceSessionCreate,
    TraceSessionResponse,
    DiagnosisResponse,
    ApplyPatchRequest,
    ApplyPatchResponse,
)
from epilog.api.services.diagnosis.provider import BaseDiagnosisProvider
from epilog.api.services.diagnosis.gemini_provider import GeminiProvider
from epilog.api.services.diagnosis.engine import DiagnosisEngine
from epilog.api.services.patch_applier import PatchApplier
from epilog.db.models import TraceEvent, TraceSession

router = APIRouter()


def get_diagnosis_engine() -> DiagnosisEngine:
    api_key = settings.google_api_key
    if not api_key:
        provider = None
    else:
        provider = GeminiProvider(api_key=api_key)
    
    return DiagnosisEngine(provider) if provider else None


@router.post("/events/{event_id}/diagnose", response_model=DiagnosisResponse)
async def diagnose_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    engine: Optional[DiagnosisEngine] = Depends(get_diagnosis_engine),
):
    """Trigger AI diagnosis for a specific event."""
    if not engine:
        raise HTTPException(
            status_code=500, 
            detail="Diagnosis engine not configured. Please set GOOGLE_API_KEY."
        )
    
    try:
        result = await engine.run_diagnosis(db, event_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnosis failed: {str(e)}")


@router.post("/apply-patch", response_model=ApplyPatchResponse)
async def apply_patch(
    request: ApplyPatchRequest,
):
    """Apply a generated code patch to the local filesystem."""
    project_root = settings.epilog_project_path
    if not project_root:
        raise HTTPException(
            status_code=500, 
            detail="EPILOG_PROJECT_PATH not set. Cannot apply patch."
        )

    success = PatchApplier.apply_patch(
        project_root=project_root,
        file_path=request.file_path,
        diff_content=request.diff_content
    )

    if success:
        return ApplyPatchResponse(success=True, message="Patch applied successfully.")
    else:
        return ApplyPatchResponse(success=False, message="Failed to apply patch.")


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

    return Response(content=event.screenshot, media_type="image/jpeg")


@router.get("/sessions/{session_id}/events/stream")
async def stream_session_events(
    session_id: UUID,
    db_factory=Depends(lambda: get_db),
) -> StreamingResponse:
    """Stream events for a specific session using Server-Sent Events (SSE)."""

    async def event_generator() -> AsyncGenerator[str, None]:
        last_event_id = 0
        
        # Initial check to see if session exists
        async for db in db_factory():
            result = await db.execute(select(TraceSession).where(TraceSession.id == session_id))
            if not result.scalar_one_or_none():
                yield f"data: {json.dumps({'error': 'Session not found'})}\n\n"
                return

        while True:
            try:
                async for db in db_factory():
                    # Query for new events since last_event_id
                    stmt = (
                        select(TraceEvent)
                        .where(TraceEvent.session_id == session_id)
                        .where(TraceEvent.id > last_event_id)
                        .order_by(TraceEvent.id.asc())
                    )
                    result = await db.execute(stmt)
                    events = result.scalars().all()

                    for event in events:
                        last_event_id = event.id
                        # Prepare data for SSE
                        data = {
                            "id": event.id,
                            "run_id": str(event.run_id),
                            "event_type": event.event_type,
                            "timestamp": event.timestamp.isoformat(),
                            "event_data": event.event_data,
                            "has_screenshot": event.screenshot is not None,
                        }
                        yield f"data: {json.dumps(data)}\n\n"

                # Keep-alive heartbeats every 15 seconds if no new data
                # Or just sleep for a bit to poll
                await asyncio.sleep(1.0)
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        },
    )
