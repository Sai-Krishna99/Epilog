# patient_agent.py
import asyncio
import uuid
import base64
import os
from epilog.sdk import EpilogCallbackHandler as Epilog

# Demo Asset Paths
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "demo_assets")
PATH_LIST = os.path.join(ASSETS_DIR, "patient_list.png")
PATH_SURGERY = os.path.join(ASSETS_DIR, "surgery_ui.png")

def get_b64(path):
    """Load image from disk and return base64 string."""
    if not os.path.exists(path):
        print(f"Warning: Asset not found at {path}")
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

async def main():
    # Load assets
    list_b64 = get_b64(PATH_LIST)
    surgery_b64 = get_b64(PATH_SURGERY)

    # Initialize Epilog
    epilog = Epilog(
        api_base_url="http://localhost:8000",
        session_name="Patient Agent Production Demo"
    )
    
    # Start the session
    session_id = await epilog.start_session()
    if not session_id:
        print("Failed to start Epilog session. Is the server running?")
        return

    print(f"Starting Simulation (Session: {session_id})...")
    
    # 1. Simulate a successful step with a screenshot of the patient list
    run_id = uuid.uuid4()
    await epilog.on_tool_end(
        output="Patient list successfully loaded: [Sai Krishna, Jane Doe, John Smith]", 
        run_id=run_id,
        screenshot_base64=list_b64
    )
    await asyncio.sleep(1)
    
    # 2. Simulate a failure with a surgery UI screenshot (Visual Mismatch)
    err_id = uuid.uuid4()
    print("Recording failure with visual mismatched screenshot...")
    await epilog.on_tool_error(
        error=RuntimeError("Timeout: Could not find element with text 'Submit' to proceed to final check-in."),
        run_id=err_id,
        screenshot_base64=surgery_b64
    )
    
    # Ensure all events are sent before finishing
    await epilog.flush()
    print("\n--- Simulation Complete ---")
    print("AI Visual Mismatch recorded. Go to the Dashboard and hit DIAGNOSE!")

if __name__ == "__main__":
    asyncio.run(main())
