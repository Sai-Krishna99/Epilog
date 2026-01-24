"""End-to-end integration tests for Epilog."""

import asyncio
import os
import time
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from epilog.sdk import EpilogCallbackHandler, ScreenshotCapture
from epilog.db.models import TraceSession, TraceEvent

# Use local postgres from docker
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
)
API_URL = "http://localhost:8000"


@pytest.fixture
async def db_engine():
    engine = create_async_engine(DATABASE_URL)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    async_session = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


@pytest.mark.asyncio
async def test_full_trace_flow(db_session):
    """Verify that a full agent trace with a screenshot reaches the database."""
    # 1. Initialize SDK components
    async with ScreenshotCapture() as capture:
        handler = EpilogCallbackHandler(
            API_URL, 
            session_name="Integration Test Session",
            screenshot_capture=capture
        )
        
        # 2. Start session (SDK -> API -> DB)
        session_id = await handler.start_session()
        assert session_id is not None
        
        # 3. Simulate agent events
        run_id = uuid4()
        
        # Chain start
        await handler.on_chain_start(
            {"name": "test_agent"}, 
            {"input": "what is the weather?"}, 
            run_id=run_id
        )
        
        # Tool execution with screenshot
        # We'll use example.com for a real capture
        await handler.on_tool_end_with_screenshot(
            "The weather is sunny in ExampleLand.",
            run_id=uuid4(),
            parent_run_id=run_id,
            url="https://example.com"
        )
        
        # Chain end
        await handler.on_chain_end(
            {"output": "It is sunny."}, 
            run_id=run_id
        )
        
        # 4. Flush and wait for background worker
        await handler.flush()
        
    # 5. Verify Database State
    # Check session exists
    stmt = select(TraceSession).where(TraceSession.id == session_id)
    result = await db_session.execute(stmt)
    db_session_record = result.scalar_one_or_none()
    assert db_session_record is not None
    assert db_session_record.name == "Integration Test Session"
    
    # Check events count
    stmt = select(func.count(TraceEvent.id)).where(TraceEvent.session_id == session_id)
    result = await db_session.execute(stmt)
    event_count = result.scalar()
    assert event_count == 3 # chain_start, tool_end (with screenshot), chain_end
    
    # Check screenshot exists
    stmt = select(TraceEvent).where(
        TraceEvent.session_id == session_id,
        TraceEvent.event_type == "tool_end"
    )
    result = await db_session.execute(stmt)
    tool_event = result.scalar_one()
    assert tool_event.screenshot is not None
    assert len(tool_event.screenshot) > 1000 # Should be a few KB after compression
    
    print(f"\nIntegration Test Passed: Session {session_id} verified in DB.")
