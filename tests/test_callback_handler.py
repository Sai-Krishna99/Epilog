"""Tests for EpilogCallbackHandler."""

import asyncio
import time
from uuid import uuid4

import pytest
import respx
from httpx import Response

from epilog.sdk.callback_handler import EpilogCallbackHandler


@pytest.fixture
async def handler():
    """Fixture for EpilogCallbackHandler with a pre-set session_id."""
    h = EpilogCallbackHandler("http://localhost:8000")
    h.session_id = uuid4()
    # Speed up cooldown for testing
    h.cooldown_period = 0.5
    yield h
    # Cleanup worker task if started
    if h.worker_task and not h.worker_task.done():
        h.worker_task.cancel()
        try:
            await h.worker_task
        except asyncio.CancelledError:
            pass
    await h.client.close()


@pytest.mark.asyncio
async def test_callback_latency(handler):
    """Verify that callback methods return almost immediately."""
    start_time = time.perf_counter()
    await handler.on_tool_start(
        {"name": "test_tool"}, 
        "test input", 
        run_id=uuid4()
    )
    elapsed = (time.perf_counter() - start_time) * 1000
    
    assert elapsed < 100, f"Callback took {elapsed:.2f}ms, should be <100ms"
    assert handler.queue.qsize() == 1


@pytest.mark.asyncio
async def test_worker_ingestion(handler):
    """Verify that the background worker sends events to the API."""
    async with respx.mock(base_url="http://localhost:8000/api/v1/traces") as respx_mock:
        respx_mock.post("/events").mock(return_value=Response(201, json={"id": 123}))
        
        handler.worker_task = asyncio.create_task(handler._worker())
        
        await handler.on_tool_start(
            {"name": "test_tool"}, 
            "test input", 
            run_id=uuid4()
        )
        
        # Wait for worker to process
        await handler.flush()
        
        assert len(respx_mock.calls) == 1
        assert handler.queue.empty()


@pytest.mark.asyncio
async def test_circuit_breaker(handler):
    """Verify that the circuit breaker pauses ingestion after multiple failures."""
    async with respx.mock(base_url="http://localhost:8000/api/v1/traces") as respx_mock:
        # Mock 500 errors
        respx_mock.post("/events").mock(return_value=Response(500))
        
        handler.worker_task = asyncio.create_task(handler._worker())
        
        # Send 3 events (max_failures)
        for _ in range(3):
            await handler.on_tool_start({"name": "fail"}, "input", run_id=uuid4())
            
        await handler.flush()
        
        assert len(respx_mock.calls) == 3
        assert handler.failed_count == 3
        assert time.time() < handler.cooldown_until
        
        # Send another event - should NOT result in an API call due to cooldown
        await handler.on_tool_start({"name": "cooldown"}, "input", run_id=uuid4())
        await handler.flush()
        
        assert len(respx_mock.calls) == 3 # Still 3


@pytest.mark.asyncio
async def test_drop_oldest(handler):
    """Verify that the queue drops the oldest event when full."""
    # Reset queue with small size
    handler.queue = asyncio.Queue(maxsize=2)
    
    # Fill queue
    await handler.on_tool_start({"name": "1"}, "i1", run_id=uuid4())
    await handler.on_tool_start({"name": "2"}, "i2", run_id=uuid4())
    assert handler.queue.qsize() == 2
    
    # Add 3rd event - should drop "1" (oldest)
    await handler.on_tool_start({"name": "3"}, "i3", run_id=uuid4())
    assert handler.queue.qsize() == 2
    
    # Check item 1 is "2"
    item1 = handler.queue.get_nowait()
    assert item1["event_data"]["tool"] == "2"
    
    item2 = handler.queue.get_nowait()
    assert item2["event_data"]["tool"] == "3"
