import os
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from epilog.api.services.diagnosis.provider import BaseDiagnosisProvider, DiagnosisReport
from epilog.db.models import TraceEvent, TraceSession
from epilog.db.session import settings

class DiagnosisEngine:
    def __init__(self, provider: BaseDiagnosisProvider):
        self.provider = provider

    async def run_diagnosis(
        self, 
        db: AsyncSession, 
        event_id: int,
        window_size: int = 5
    ) -> Dict[str, Any]:
        """
        Orchestrates the full diagnosis loop for a specific event.
        """
        # 1. Fetch the target event
        target_event = await db.get(TraceEvent, event_id)
        if not target_event:
            raise ValueError(f"Event {event_id} not found")

        # 2. Fetch context (temporal window)
        # Get events from the same session, ordered by id, before the target
        session_id = target_event.session_id
        stmt = (
            select(TraceEvent)
            .where(TraceEvent.session_id == session_id)
            .where(TraceEvent.id < target_event.id)
            .order_by(TraceEvent.id.desc())
            .limit(window_size)
        )
        result = await db.execute(stmt)
        previous_events = list(reversed(result.scalars().all()))

        # 3. Prepare data for provider
        context_data = [e.to_dict() for e in previous_events]
        target_data = target_event.to_dict()
        
        # 4. Handle multimodal input (screenshot)
        screenshot = None
        if target_event.screenshot:
            screenshot = target_event.screenshot

        # 5. Call provider for diagnosis
        diagnosis = await self.provider.diagnose(
            events=context_data,
            target_event=target_data,
            screenshot_bytes=screenshot
        )

        # 6. Optional: Generate Patch if diagnosis suggests it
        patch = None
        project_path = settings.epilog_project_path
        
        # We try to find the relevant file from metadata if possible
        # Check event_data for source_file
        file_path = target_event.event_data.get("metadata", {}).get("source_file") or "agent.py"
        
        if project_path and os.path.exists(os.path.join(project_path, file_path)):
            full_path = os.path.join(project_path, file_path)
            with open(full_path, "r") as f:
                source_code = f.read()
            
            patch = await self.provider.generate_patch(
                diagnosis=diagnosis,
                source_code=source_code,
                file_path=file_path
            )

        return {
            "diagnosis": diagnosis.model_dump(),
            "patch": patch
        }
