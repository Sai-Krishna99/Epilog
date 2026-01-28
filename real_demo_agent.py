"""
Real Demo Agent: Hacker News Scraper
====================================
This agent demonstrates a REAL failure that Epilog can diagnose.

The agent tries to scrape Hacker News headlines using an OUTDATED selector.
- Old HN used: .storylink
- Current HN uses: .titleline > a

When the agent fails, Epilog captures the screenshot showing the actual
page structure, and Gemini can identify that the selector is wrong.

Usage:
    # Start the API first
    export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/epilog"
    uv run uvicorn epilog.api.main:app --reload

    # Then run this demo
    uv run python real_demo_agent.py

    # Go to http://localhost:3000 and click DIAGNOSE on the error event
"""

import asyncio
import uuid
from epilog.sdk import EpilogCallbackHandler, ScreenshotCapture


# The WRONG selector (this is the old HN class, no longer exists)
WRONG_SELECTOR = ".storylink"

# The CORRECT selector (what HN actually uses now)
CORRECT_SELECTOR = ".titleline > a"


async def main():
    print("=" * 60)
    print(" REAL DEMO: Hacker News Scraper Agent")
    print("=" * 60)
    print()
    print("This agent will FAIL because it uses an outdated CSS selector.")
    print("Epilog will capture the failure and Gemini will diagnose it.")
    print()

    async with ScreenshotCapture(headless=True) as capture:
        # Initialize Epilog with screenshot capture
        handler = EpilogCallbackHandler(
            api_base_url="http://localhost:8000",
            session_name="Real Demo - HN Scraper (Wrong Selector)",
            screenshot_capture=capture,
        )

        # Start the session
        session_id = await handler.start_session()
        if not session_id:
            print("ERROR: Could not start Epilog session.")
            print("Make sure the API is running: uv run uvicorn epilog.api.main:app --reload")
            return

        print(f"[Session Started] {session_id}")
        print()

        # === AGENT EXECUTION ===

        chain_run_id = uuid.uuid4()

        # Step 1: Start the scraping chain
        print("[1/4] Starting HN scraper chain...")
        await handler.on_chain_start(
            serialized={"name": "HackerNewsScraper"},
            inputs={"task": "Extract the #1 headline from Hacker News"},
            run_id=chain_run_id,
        )

        # Step 2: Navigate to Hacker News
        nav_run_id = uuid.uuid4()
        print("[2/4] Navigating to news.ycombinator.com...")
        await handler.on_tool_start(
            serialized={"name": "browser_navigate"},
            input_str="Navigate to https://news.ycombinator.com",
            run_id=nav_run_id,
            parent_run_id=chain_run_id,
        )

        # Capture the actual page with screenshot
        await handler.on_tool_end_with_screenshot(
            output="Successfully loaded Hacker News homepage",
            run_id=nav_run_id,
            parent_run_id=chain_run_id,
            url="https://news.ycombinator.com",
        )
        print("       Page loaded and screenshot captured!")

        # Step 3: Try to extract headline with WRONG selector
        extract_run_id = uuid.uuid4()
        print(f"[3/4] Extracting headline with selector: {WRONG_SELECTOR}")
        await handler.on_tool_start(
            serialized={"name": "browser_extract"},
            input_str=f"Extract text from element matching selector '{WRONG_SELECTOR}'",
            run_id=extract_run_id,
            parent_run_id=chain_run_id,
        )

        # Simulate the failure - element not found
        # In a real agent, this would be an actual Playwright error
        error_message = (
            f"ElementNotFoundError: No element found matching selector '{WRONG_SELECTOR}'. "
            f"The page was loaded successfully but the expected element does not exist. "
            f"This may indicate the page structure has changed."
        )

        # Capture screenshot at the moment of failure
        print("[4/4] Recording failure with screenshot...")
        await handler.on_tool_error(
            error=Exception(error_message),
            run_id=extract_run_id,
            parent_run_id=chain_run_id,
        )

        # Also capture a screenshot showing the page at failure time
        # We do this via on_tool_end_with_screenshot with the error context
        screenshot_run_id = uuid.uuid4()
        await handler.on_tool_end_with_screenshot(
            output=f"FAILURE STATE: {error_message}",
            run_id=screenshot_run_id,
            parent_run_id=chain_run_id,
            url="https://news.ycombinator.com",
        )

        # End the chain with failure
        await handler.on_chain_error(
            error=Exception(f"Scraping failed: {error_message}"),
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
    print(f"  1. Agent navigated to Hacker News")
    print(f"  2. Agent tried to find elements with selector: {WRONG_SELECTOR}")
    print(f"  3. Agent FAILED because HN now uses: {CORRECT_SELECTOR}")
    print(f"  4. Epilog captured screenshots showing the actual page")
    print()
    print("Next steps:")
    print("  1. Open http://localhost:3000")
    print("  2. Select 'Real Demo - HN Scraper (Wrong Selector)' session")
    print("  3. Click DIAGNOSE on the error event")
    print("  4. Watch Gemini identify the visual mismatch!")
    print()
    print("Gemini should see:")
    print("  - Agent expected: .storylink")
    print("  - Screenshot shows: Headlines are in .titleline elements")
    print("  - Suggested fix: Update selector to '.titleline > a'")
    print()


if __name__ == "__main__":
    asyncio.run(main())
