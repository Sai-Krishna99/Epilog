"""LangChain Callback Handler for Epilog."""

import asyncio
import base64
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union
from uuid import UUID

from langchain_core.callbacks.base import AsyncCallbackHandler
from langchain_core.messages import BaseMessage
from langchain_core.outputs import LLMResult

from epilog.sdk.client import EpilogClient
from epilog.sdk.screenshot import ScreenshotCapture, compress_image

logger = logging.getLogger("epilog.sdk.callbacks")


def truncate(value: Any, max_length: int = 1000) -> str:
    """Truncate string representation of value."""
    str_val = str(value)
    if len(str_val) > max_length:
        return str_val[:max_length] + "..."
    return str_val


class EpilogCallbackHandler(AsyncCallbackHandler):
    """Callback handler that sends traces to Epilog with buffered ingestion."""

    def __init__(
        self,
        api_base_url: str,
        session_name: Optional[str] = None,
        queue_size: int = 1000,
        timeout: float = 5.0,
        screenshot_capture: Optional[ScreenshotCapture] = None,
    ):
        """Initialize the callback handler.

        Args:
            api_base_url: Base URL of the Epilog API
            session_name: Optional name for the session
            queue_size: Maximum number of events to buffer
            timeout: API request timeout
            screenshot_capture: Optional ScreenshotCapture instance for visual artifacts
        """
        self.client = EpilogClient(api_base_url, timeout=timeout)
        self.session_name = session_name
        self.session_id: Optional[UUID] = None
        self.screenshot_capture = screenshot_capture
        
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=queue_size)
        self.worker_task: Optional[asyncio.Task] = None
        
        # Circuit breaker state
        self.failed_count = 0
        self.cooldown_until = 0.0
        self.max_failures = 3
        self.cooldown_period = 60.0

    async def start_session(self) -> Optional[UUID]:
        """Start a new trace session and begin worker task.

        Returns:
            The session ID as a UUID, or None if failed
        """
        if not self.session_id:
            self.session_id = await self.client.create_session(name=self.session_name)
            
        if self.session_id and not self.worker_task:
            self.worker_task = asyncio.create_task(self._worker())
            
        return self.session_id

    async def _worker(self):
        """Background worker to process the event queue."""
        logger.info("Epilog SDK background worker started")
        try:
            while True:
                event = await self.queue.get()
                try:
                    # Check circuit breaker
                    if time.time() < self.cooldown_until:
                        # Log once when entering cooldown would be nice, 
                        # but avoiding spam for now
                        continue

                    success = await self.client.send_event(event)
                    
                    if success:
                        self.failed_count = 0
                    else:
                        self._handle_failure()
                except Exception as e:
                    logger.error(f"Error in Epilog worker sending event: {e}")
                    self._handle_failure()
                finally:
                    self.queue.task_done()
        except asyncio.CancelledError:
            logger.info("Epilog SDK worker task cancelled")
        except Exception as e:
            logger.critical(f"Epilog SDK worker task crashed: {e}")

    def _handle_failure(self):
        """Update circuit breaker state on failure."""
        self.failed_count += 1
        if self.failed_count >= self.max_failures:
            logger.warning(
                f"Epilog SDK: {self.failed_count} failures. "
                f"Cooling down for {self.cooldown_period}s."
            )
            self.cooldown_until = time.time() + self.cooldown_period

    def _enqueue_event(
        self, 
        event_type: str, 
        run_id: UUID, 
        parent_run_id: Optional[UUID], 
        data: Dict[str, Any],
        screenshot_base64: Optional[str] = None,
    ):
        """Safely enqueue an event into the buffered queue."""
        if not self.session_id:
            return

        event = {
            "session_id": str(self.session_id),
            "run_id": str(run_id),
            "parent_run_id": str(parent_run_id) if parent_run_id else None,
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "event_data": data,
            "screenshot_base64": screenshot_base64,
        }

        try:
            self.queue.put_nowait(event)
        except asyncio.QueueFull:
            # "Drop oldest" policy
            try:
                self.queue.get_nowait()
                self.queue.task_done()
                self.queue.put_nowait(event)
                logger.debug("Epilog SDK queue full, dropped oldest event")
            except (asyncio.QueueEmpty, ValueError):
                pass
        except Exception as e:
            logger.error(f"Failed to enqueue Epilog event: {e}")

    async def flush(self):
        """Wait for all pending events in the queue to be processed."""
        if self.queue.empty():
            return
        await self.queue.join()

    # --- Epilog Helpers ---

    async def capture_screenshot(
        self, 
        url: Optional[str] = None, 
        page: Any = None, 
        full_page: bool = False
    ) -> Optional[str]:
        """Capture a screenshot from a URL or Page object.

        Returns:
            Base64 encoded string or None if failed
        """
        if not self.screenshot_capture:
            return None

        try:
            if page:
                screenshot_bytes = await self.screenshot_capture.capture_page(
                    page, full_page=full_page
                )
            elif url:
                screenshot_bytes = await self.screenshot_capture.capture_url(
                    url, full_page=full_page
                )
            else:
                return None

            return base64.b64encode(screenshot_bytes).decode("utf-8")
        except Exception as e:
            logger.error(f"Screenshot capture failed: {e}")
            return None

    async def on_tool_end_with_screenshot(
        self,
        output: Any,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        url: Optional[str] = None,
        page: Any = None,
        full_page: bool = False,
        **kwargs: Any,
    ) -> None:
        """Call this explicitly if you want to capture a screenshot on tool completion."""
        screenshot_base64 = await self.capture_screenshot(
            url=url, page=page, full_page=full_page
        )
        
        self._enqueue_event(
            "tool_end",
            run_id,
            parent_run_id,
            {"output": truncate(output), "importance": "high"},
            screenshot_base64=screenshot_base64,
        )

    # --- LangChain Callback Methods ---

    async def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        self._enqueue_event(
            "chain_start",
            run_id,
            parent_run_id,
            {
                "name": serialized.get("name") or "chain",
                "inputs": truncate(inputs),
                "tags": tags,
                "metadata": metadata,
                "importance": "medium",
            },
        )

    async def on_chain_end(
        self,
        outputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        self._enqueue_event(
            "chain_end",
            run_id,
            parent_run_id,
            {"outputs": truncate(outputs), "importance": "high"},
        )

    async def on_chain_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        self._enqueue_event(
            "chain_error",
            run_id,
            parent_run_id,
            {
                "error": str(error),
                "error_type": type(error).__name__,
                "importance": "critical",
            },
        )

    async def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        self._enqueue_event(
            "tool_start",
            run_id,
            parent_run_id,
            {
                "tool": serialized.get("name") or "tool",
                "input": truncate(input_str),
                "tags": tags,
                "metadata": metadata,
                "importance": "high",
            },
        )

    async def on_tool_end(
        self,
        output: Any,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        self._enqueue_event(
            "tool_end",
            run_id,
            parent_run_id,
            {"output": truncate(output), "importance": "high"},
        )

    async def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        self._enqueue_event(
            "tool_error",
            run_id,
            parent_run_id,
            {
                "error": str(error),
                "error_type": type(error).__name__,
                "importance": "critical",
            },
        )

    async def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        self._enqueue_event(
            "llm_start",
            run_id,
            parent_run_id,
            {
                "model": serialized.get("name") or "llm",
                "prompt_count": len(prompts),
                "importance": "medium",
            },
        )

    async def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        self._enqueue_event(
            "llm_end",
            run_id,
            parent_run_id,
            {
                "generations": len(response.generations) if response.generations else 0,
                "importance": "medium",
            },
        )

    async def on_agent_action(
        self,
        action: Any,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        self._enqueue_event(
            "agent_action",
            run_id,
            parent_run_id,
            {
                "tool": action.tool,
                "tool_input": truncate(str(action.tool_input)),
                "importance": "high",
            },
        )

    async def on_agent_finish(
        self,
        finish: Any,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        self._enqueue_event(
            "agent_finish",
            run_id,
            parent_run_id,
            {"return_values": truncate(str(finish.return_values)), "importance": "high"},
        )
