import httpx
import json
import os
import base64
from typing import List, Optional, Dict, Any
from .provider import BaseDiagnosisProvider, DiagnosisReport

class GeminiProvider(BaseDiagnosisProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        # Using Google AI Studio endpoint (free tier)
        self.diagnosis_model_name = os.getenv("EPILOG_DIAGNOSIS_MODEL", "gemini-3-flash-preview")
        self.patch_model_name = os.getenv("EPILOG_PATCH_MODEL", "gemini-3-flash-preview")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    async def _generate_content(self, model: str, parts: List[Dict[str, Any]], response_mime_type: Optional[str] = None) -> str:
        url = f"{self.base_url}/{model}:generateContent"

        payload = {
            "contents": [{"role": "user", "parts": parts}]
        }

        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": self.api_key
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code != 200:
                raise Exception(f"Gemini API Error {response.status_code}: {response.text}")

            data = response.json()
            try:
                # generateContent returns a single object with candidates
                full_text = data["candidates"][0]["content"]["parts"][0]["text"]
                return full_text
            except (KeyError, IndexError) as e:
                raise Exception(f"Unexpected response format: {str(e)} - Raw: {response.text[:200]}")

    async def diagnose(
        self, 
        events: List[Dict[str, Any]], 
        target_event: Dict[str, Any],
        screenshot_bytes: Optional[bytes] = None
    ) -> DiagnosisReport:
        
        # Prepare content window context
        context_str = json.dumps(events, indent=2)
        target_str = json.dumps(target_event, indent=2)
        
        prompt = f"""
        You are an expert AI Debugger. 
        Analyze the following execution trace events leading up to a failure.
        
        RECENT CONTEXT:
        {context_str}
        
        TARGET EVENT (WHERE FAILURE OCCURRED):
        {target_str}
        
        TASK:
        Compare the 'thought' or 'action' in the Target Event with the provided screenshot (if any).
        Identify if there is a mismatch between what the agent intended to do and what happened visually.
        
        OUTPUT FORMAT:
        Return a JSON object with:
        - incident_summary: Concise description of the failure.
        - visual_mismatch_identified: Boolean.
        - explanation: Detailed explanation of the mismatch or failure.
        - suggested_fix_logic: High-level logic required to fix the code.
        """
        
        parts = [{"text": prompt}]
        if screenshot_bytes:
            # Simple mime type detection from bytes header
            mime_type = "image/jpeg"
            if screenshot_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
                mime_type = "image/png"
            elif screenshot_bytes.startswith(b"GIF87a") or screenshot_bytes.startswith(b"GIF89a"):
                mime_type = "image/gif"
            
            parts.append({
                "inline_data": {
                    "mime_type": mime_type,
                    "data": base64.b64encode(screenshot_bytes).decode("utf-8")
                }
            })
            
        try:
            text = await self._generate_content(
                model=self.diagnosis_model_name,
                parts=parts,
                response_mime_type="application/json"
            )
        except Exception as e:
            return DiagnosisReport(
                incident_summary="AI Generation Error",
                visual_mismatch_identified=False,
                explanation=f"Diagnosis generation failed: {str(e)}",
                suggested_fix_logic="Manual review required."
            )
        
        # Parse JSON from response
        try:
            # Clean up potential markdown wrapping from 3.0 preview
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].strip()
            data = json.loads(text)
            return DiagnosisReport(**data)
        except Exception as e:
            # Fallback for parsing errors
            return DiagnosisReport(
                incident_summary="AI Analysis Error",
                visual_mismatch_identified=False,
                explanation=f"Failed to parse Gemini response: {str(e)}",
                suggested_fix_logic="Manual review required."
            )

    async def generate_patch(
        self, 
        diagnosis: DiagnosisReport, 
        source_code: str,
        file_path: str
    ) -> str:
        
        prompt = f"""
        You are an expert Software Engineer (Auto-Surgeon).
        A multimodal agent failed with the following diagnosis:
        
        DIAGNOSIS:
        {diagnosis.explanation}
        
        FIX LOGIC:
        {diagnosis.suggested_fix_logic}
        
        SOURCE CODE (from {file_path}):
        ```python
        {source_code}
        ```
        
        TASK:
        Generate a Standard Unified Diff patch that fixes the bug.
        The patch should be grounded in the visual mismatch identified.
        Ensure the diff is valid and can be applied with the `patch` utility.
        
        OUTPUT:
        Return ONLY the raw Unified Diff string. No commentary.
        """
        
        try:
            text = await self._generate_content(
                model=self.patch_model_name,
                parts=[{"text": prompt}]
            )
        except Exception as e:
            return f"Error generating patch: {str(e)}"
        
        # Clean up output
        if "```diff" in text:
            text = text.split("```diff")[1].split("```")[0].strip()
        elif "```" in text:
            segments = text.split("```")
            if len(segments) > 1:
                text = segments[1].strip()
            
        return text.strip()
