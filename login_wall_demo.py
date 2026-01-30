"""
Login Wall Demo: LinkedIn Profile Scraper
==========================================
This demo shows a DRAMATICALLY visible failure - a login wall
blocking access to profile content.

The agent tries to scrape a LinkedIn profile,
but gets redirected to the login page instead.

The visual mismatch is immediately obvious:
- Agent says: "Looking for profile data (name, title)"
- Screenshot shows: "Sign in to view this profile" page

Usage:
    # Start the API first
    export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/epilog"
    uv run uvicorn epilog.api.main:app --reload

    # Then run this demo
    uv run python login_wall_demo.py

    # Go to http://localhost:3000 and click DIAGNOSE on the error event

WARNING: LinkedIn may rate-limit or block repeated requests.
         Use sparingly and consider the pre-recorded fallback.
"""

import asyncio
import uuid
from epilog.sdk import EpilogCallbackHandler, ScreenshotCapture


# Use a public profile URL (LinkedIn will redirect to login anyway)
TARGET_URL = "https://www.linkedin.com/in/sundarpichai/"
PROFILE_NAME_SELECTOR = ".text-heading-xlarge"


async def main():
    print("=" * 60)
    print(" LOGIN WALL DEMO: LinkedIn Profile Scraper")
    print("=" * 60)
    print()
    print("This agent will try to scrape a LinkedIn profile, but will")
    print("be redirected to a login wall instead of the profile content.")
    print()
    print("WARNING: Use sparingly - LinkedIn may rate-limit repeated requests.")
    print()

    async with ScreenshotCapture(headless=True) as capture:
        handler = EpilogCallbackHandler(
            api_base_url="http://localhost:8000",
            session_name="Login Wall Demo - LinkedIn Scraper",
            screenshot_capture=capture,
        )

        session_id = await handler.start_session()
        if not session_id:
            print("ERROR: Could not start Epilog session.")
            print("Make sure the API is running: uv run uvicorn epilog.api.main:app --reload")
            return

        print(f"[Session Started] {session_id}")
        print()

        # === AGENT EXECUTION ===

        chain_run_id = uuid.uuid4()

        # Step 1: Start the profile scraping chain
        print("[1/4] Starting LinkedIn profile scraper chain...")
        await handler.on_chain_start(
            serialized={"name": "LinkedInProfileScraper"},
            inputs={"task": "Extract name and job title from LinkedIn profile"},
            run_id=chain_run_id,
        )

        # Step 2: Navigate to LinkedIn profile
        nav_run_id = uuid.uuid4()
        print("[2/4] Navigating to LinkedIn profile...")
        await handler.on_tool_start(
            serialized={"name": "browser_navigate"},
            input_str=f"Navigate to {TARGET_URL}",
            run_id=nav_run_id,
            parent_run_id=chain_run_id,
        )

        # Capture the page - this should show the login wall!
        await handler.on_tool_end_with_screenshot(
            output="Page loaded - attempting to access profile",
            run_id=nav_run_id,
            parent_run_id=chain_run_id,
            url=TARGET_URL,
        )
        print("       Page loaded and screenshot captured!")
        print("       (Screenshot should show login/auth wall)")

        # Step 3: Try to extract profile name
        extract_run_id = uuid.uuid4()
        print(f"[3/4] Attempting to extract profile name with selector: {PROFILE_NAME_SELECTOR}")
        await handler.on_tool_start(
            serialized={"name": "browser_extract"},
            input_str=f"Extract profile name from element matching '{PROFILE_NAME_SELECTOR}'",
            run_id=extract_run_id,
            parent_run_id=chain_run_id,
        )

        # Simulate the failure - profile content not accessible
        error_message = (
            f"AuthenticationRequiredError: Cannot access profile content. "
            f"Selector '{PROFILE_NAME_SELECTOR}' not found. "
            f"The page appears to require authentication to view this profile."
        )

        # Record the failure with screenshot
        print("[4/4] Recording failure with screenshot...")
        await handler.on_tool_error(
            error=Exception(error_message),
            run_id=extract_run_id,
            parent_run_id=chain_run_id,
        )

        # Capture another screenshot at failure time
        screenshot_run_id = uuid.uuid4()
        await handler.on_tool_end_with_screenshot(
            output=f"FAILURE STATE: {error_message}",
            run_id=screenshot_run_id,
            parent_run_id=chain_run_id,
            url=TARGET_URL,
        )

        # End the chain with failure
        await handler.on_chain_error(
            error=Exception(f"Profile scraping failed: {error_message}"),
            run_id=chain_run_id,
        )

        # Flush all events
        await handler.flush()

    print()
    print("=" * 60)
    print(" DEMO COMPLETE")
    print("=" * 60)
    print()
    print("What happened:")
    print("  1. Agent navigated to LinkedIn profile URL")
    print("  2. LinkedIn redirected to login/auth wall")
    print("  3. Agent tried to find profile name element")
    print("  4. Agent FAILED because content requires authentication")
    print()
    print("The Visual Mismatch:")
    print("  - Agent expected: Profile with name and title")
    print("  - Screenshot shows: Login wall / 'Sign in to view' page")
    print("  - Gemini should say: 'Authentication required - login wall blocking content'")
    print()
    print("Next steps:")
    print("  1. Open http://localhost:3000")
    print("  2. Select 'Login Wall Demo - LinkedIn Scraper' session")
    print("  3. Click DIAGNOSE on the error event")
    print("  4. See Gemini identify the login wall!")
    print()


if __name__ == "__main__":
    asyncio.run(main())
