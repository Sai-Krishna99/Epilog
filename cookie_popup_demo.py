"""
Cookie Popup Demo: News Scraper
===============================
This demo shows a DRAMATICALLY visible failure - a cookie consent modal
blocking the entire page content.

The agent tries to scrape article content from a news site,
but a GDPR cookie consent popup blocks everything.

The visual mismatch is immediately obvious:
- Agent says: "Looking for article content"
- Screenshot shows: Giant cookie consent modal blocking the entire page

Usage:
    # Start the API first
    export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/epilog"
    uv run uvicorn epilog.api.main:app --reload

    # Then run this demo
    uv run python cookie_popup_demo.py

    # Go to http://localhost:3000 and click DIAGNOSE on the error event
"""

import asyncio
import uuid
from epilog.sdk import EpilogCallbackHandler, ScreenshotCapture


TARGET_URL = "https://www.theguardian.com/world"
ARTICLE_SELECTOR = ".dcr-1ay6c8e"  # Guardian article card class


async def main():
    print("=" * 60)
    print(" COOKIE POPUP DEMO: News Scraper")
    print("=" * 60)
    print()
    print("This agent will try to scrape The Guardian, but a cookie consent")
    print("modal will block the entire page content.")
    print()
    print("The visual mismatch will be IMMEDIATELY obvious in the screenshot!")
    print()

    async with ScreenshotCapture(headless=True) as capture:
        handler = EpilogCallbackHandler(
            api_base_url="http://localhost:8000",
            session_name="Cookie Popup Demo - News Scraper",
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

        # Step 1: Start the scraping chain
        print("[1/4] Starting news scraper chain...")
        await handler.on_chain_start(
            serialized={"name": "NewsArticleScraper"},
            inputs={"task": "Extract top news headlines from The Guardian"},
            run_id=chain_run_id,
        )

        # Step 2: Navigate to The Guardian
        nav_run_id = uuid.uuid4()
        print("[2/4] Navigating to The Guardian...")
        await handler.on_tool_start(
            serialized={"name": "browser_navigate"},
            input_str=f"Navigate to {TARGET_URL}",
            run_id=nav_run_id,
            parent_run_id=chain_run_id,
        )

        # Capture the page - this should show the cookie consent modal!
        await handler.on_tool_end_with_screenshot(
            output="Page loaded - attempting to access content",
            run_id=nav_run_id,
            parent_run_id=chain_run_id,
            url=TARGET_URL,
        )
        print("       Page loaded and screenshot captured!")
        print("       (Screenshot should show cookie consent modal)")

        # Step 3: Try to extract article headlines
        extract_run_id = uuid.uuid4()
        print(f"[3/4] Attempting to extract headlines with selector: {ARTICLE_SELECTOR}")
        await handler.on_tool_start(
            serialized={"name": "browser_extract"},
            input_str=f"Extract text from news article elements matching '{ARTICLE_SELECTOR}'",
            run_id=extract_run_id,
            parent_run_id=chain_run_id,
        )

        # Simulate the failure - content not accessible due to modal
        error_message = (
            f"ContentNotAccessibleError: Cannot interact with article elements. "
            f"Selector '{ARTICLE_SELECTOR}' found 0 visible elements. "
            f"The page content may be obscured by an overlay or modal dialog."
        )

        # Record the failure with screenshot
        print("[4/4] Recording failure with screenshot...")
        await handler.on_tool_error(
            error=Exception(error_message),
            run_id=extract_run_id,
            parent_run_id=chain_run_id,
        )

        # Capture another screenshot at failure time to show the state
        screenshot_run_id = uuid.uuid4()
        await handler.on_tool_end_with_screenshot(
            output=f"FAILURE STATE: {error_message}",
            run_id=screenshot_run_id,
            parent_run_id=chain_run_id,
            url=TARGET_URL,
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
    print("  1. Agent navigated to The Guardian news page")
    print("  2. Cookie consent modal appeared (GDPR requirement)")
    print("  3. Agent tried to find article elements")
    print("  4. Agent FAILED because modal blocks all content")
    print()
    print("The Visual Mismatch:")
    print("  - Agent expected: News article headlines")
    print("  - Screenshot shows: GIANT cookie consent modal")
    print("  - Gemini should say: 'Cookie consent modal blocking page content'")
    print()
    print("Next steps:")
    print("  1. Open http://localhost:3000")
    print("  2. Select 'Cookie Popup Demo - News Scraper' session")
    print("  3. Click DIAGNOSE on the error event")
    print("  4. See Gemini identify the cookie consent issue!")
    print()


if __name__ == "__main__":
    asyncio.run(main())
