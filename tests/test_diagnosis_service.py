import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from epilog.api.services.diagnosis.engine import DiagnosisEngine
from epilog.api.services.diagnosis.provider import DiagnosisReport
from epilog.db.models import TraceEvent

@pytest.mark.asyncio
async def test_engine_windowing_logic():
    # Mock DB and Provider
    mock_db = AsyncMock()
    mock_provider = AsyncMock()
    
    # Mock Target Event
    target_event = MagicMock(spec=TraceEvent)
    target_event.id = 100
    target_event.session_id = "test-session"
    target_event.screenshot = b"fake-screenshot"
    target_event.event_data = {"metadata": {"source_file": "test.py"}}
    target_event.to_dict.return_value = {"id": 100, "data": "target"}
    
    # Mock Previous Events
    prev_event = MagicMock(spec=TraceEvent)
    prev_event.id = 99
    prev_event.to_dict.return_value = {"id": 99, "data": "prev"}
    
    mock_db.get.return_value = target_event
    
    # Mock DB execution for previous events
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [prev_event]
    mock_db.execute.return_value = mock_result
    
    # Mock Provider Diagnosis
    mock_report = DiagnosisReport(
        incident_summary="Test Success",
        visual_mismatch_identified=False,
        explanation="Everything is fine",
        suggested_fix_logic="No fix needed"
    )
    mock_provider.diagnose.return_value = mock_report
    
    engine = DiagnosisEngine(mock_provider)
    
    # Run
    result = await engine.run_diagnosis(mock_db, 100)
    
    # Verify
    assert result["diagnosis"]["incident_summary"] == "Test Success"
    mock_provider.diagnose.assert_called_once()
    
    # Check that events were passed correctly
    args, kwargs = mock_provider.diagnose.call_args
    assert len(kwargs["events"]) == 1
    assert kwargs["events"][0]["id"] == 99
    assert kwargs["screenshot_bytes"] == b"fake-screenshot"

@pytest.mark.asyncio
async def test_gemini_provider_parsing():
    from epilog.api.services.diagnosis.gemini_provider import GeminiProvider
    
    with patch("google.genai.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock Response
        mock_response = MagicMock()
        mock_response.text = '{"incident_summary": "Mock Summary", "visual_mismatch_identified": true, "explanation": "Visual mismatch found", "suggested_fix_logic": "Update selector"}'
        mock_client.models.generate_content.return_value = mock_response
        
        provider = GeminiProvider(api_key="fake-key")
        
        report = await provider.diagnose(events=[], target_event={})
        
        assert report.incident_summary == "Mock Summary"
        assert report.visual_mismatch_identified is True
