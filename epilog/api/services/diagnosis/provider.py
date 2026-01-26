from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class DiagnosisReport(BaseModel):
    incident_summary: str
    visual_mismatch_identified: bool
    explanation: str
    suggested_fix_logic: str

class BaseDiagnosisProvider(ABC):
    """
    Abstract base class for diagnosis providers.
    Allows Epilog to be model-agnostic (Gemini, OpenAI, Anthropic, etc.)
    """

    @abstractmethod
    async def diagnose(
        self, 
        events: List[Dict[str, Any]], 
        target_event: Dict[str, Any],
        screenshot_bytes: Optional[bytes] = None
    ) -> DiagnosisReport:
        """
        Analyze events and optional screenshot to provide a diagnosis.
        """
        pass

    @abstractmethod
    async def generate_patch(
        self, 
        diagnosis: DiagnosisReport, 
        source_code: str,
        file_path: str
    ) -> str:
        """
        Generate a Unified Diff patch based on the diagnosis and source code.
        """
        pass
