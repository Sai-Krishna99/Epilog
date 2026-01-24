"""HTTP client for Epilog API communication."""

import logging
from typing import Any, Dict, Optional, Union
from uuid import UUID

import httpx

logger = logging.getLogger("epilog.sdk.client")


class EpilogClient:
    """Client for interacting with the Epilog API."""

    def __init__(self, api_base_url: str, timeout: float = 5.0):
        """Initialize the Epilog client.

        Args:
            api_base_url: Base URL of the Epilog API (e.g., http://localhost:8000)
            timeout: Timeout for API requests in seconds
        """
        self.api_base_url = api_base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(
            base_url=f"{self.api_base_url}/api/v1/traces",
            timeout=self.timeout,
        )

    async def create_session(
        self, name: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[UUID]:
        """Create a new trace session.

        Args:
            name: Optional name for the session
            metadata: Optional metadata for the session

        Returns:
            The session ID as a UUID, or None if creation failed
        """
        try:
            payload = {}
            if name:
                payload["name"] = name
            if metadata:
                payload["session_metadata"] = metadata

            response = await self.client.post("/sessions", json=payload)
            response.raise_for_status()
            data = response.json()
            return UUID(data["id"])
        except Exception as e:
            logger.error(f"Failed to create Epilog session: {str(e)}")
            return None

    async def send_event(self, event: Dict[str, Any]) -> Optional[int]:
        """Send a single trace event to the API.

        Args:
            event: Event data dictionary

        Returns:
            The event ID as an integer, or None if ingestion failed
        """
        try:
            # Note: The event dictionary should already contain session_id, run_id, etc.
            # Handle screenshot_bytes if present (convert to base64 if needed, 
            # though the handler should handle this)
            response = await self.client.post("/events", json=event)
            response.raise_for_status()
            data = response.json()
            return data["id"]
        except Exception as e:
            logger.warning(f"Failed to send Epilog event: {str(e)}")
            return None

    async def close(self):
        """Close the underlying HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
