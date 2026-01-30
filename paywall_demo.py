"""
Paywall Demo: Medium Article Scraper
====================================
This demo shows another DRAMATICALLY visible failure - a paywall
blocking access to article content.

The agent tries to scrape a Medium article,
but hits the "Member-only story" wall.

The visual mismatch is immediately obvious:
- Agent says: "Extracting article content"
- Screenshot shows: "Member-only story" or "You've read all free articles"

Usage:
    uv run python paywall_demo.py
"""

import asyncio
import uuid
from epilog.sdk import EpilogCallbackHandler, ScreenshotCapture


# Medium member-only articles trigger paywall
# Using a popular member-only article
TARGET_URL = "https://medium.com/towards-data-science/yes-you-should-understand-backprop-e2f06eab496b"
ARTICLE_SELECTOR = "article p"


async def main():
    print("=" * 60)
    print(" PAYWALL DEMO: Medium Article Scraper")
    print("=" * 60)
    print()
    print("This agent will try to scrape a Medium article, but will")
    print("hit a paywall blocking the full content.")
    print()

    async with ScreenshotCapture(headless=True) as capture:
        handler = EpilogCallbackHandler(
            api_base_url="http://localhost:8000",
            session_name="Paywall Demo - Medium Scraper",
            screenshot_capture=capture,
        )

        session_id = await handler.start_session()
        if not session_id:
            print("ERROR: Could not start Epilog session.")
            print("Make sure the API is running.")
            return

        print(f"[Session Started] {session_id}")
        print()

        chain_run_id = uuid.uuid4()

        # Step 1: Start the article scraping chain
        print("[1/4] Starting Medium article scraper chain...")
        await handler.on_chain_start(
            serialized={"name": "MediumArticleScraper"},
            inputs={"task": "Extract full article content from Medium post"},
            run_id=chain_run_id,
        )

        # Step 2: Navigate to Medium article
        nav_run_id = uuid.uuid4()
        print("[2/4] Navigating to Medium article...")
        await handler.on_tool_start(
            serialized={"name": "browser_navigate"},
            input_str=f"Navigate to {TARGET_URL}",
            run_id=nav_run_id,
            parent_run_id=chain_run_id,
        )

        # Capture the page - may show paywall
        await handler.on_tool_end_with_screenshot(
            output="Page loaded - attempting to extract article",
            run_id=nav_run_id,
            parent_run_id=chain_run_id,
            url=TARGET_URL,
        )
        print("       Page loaded and screenshot captured!")

        # Step 3: Try to extract full article content
        extract_run_id = uuid.uuid4()
        print(f"[3/4] Attempting to extract article content...")
        await handler.on_tool_start(
            serialized={"name": "browser_extract"},
            input_str=f"Extract full article text from '{ARTICLE_SELECTOR}'",
            run_id=extract_run_id,
            parent_run_id=chain_run_id,
        )

        # Simulate the failure - paywall blocks full content
        error_message = (
            f"PaywallError: Cannot access full article content. "
            f"Only partial content visible. "
            f"The page shows 'Member-only story' or subscription prompt blocking full text."
        )

        print("[4/4] Recording failure with screenshot...")
        await handler.on_tool_error(
            error=Exception(error_message),
            run_id=extract_run_id,
            parent_run_id=chain_run_id,
        )

        # Capture screenshot at failure
        screenshot_run_id = uuid.uuid4()
        await handler.on_tool_end_with_screenshot(
            output=f"FAILURE STATE: {error_message}",
            run_id=screenshot_run_id,
            parent_run_id=chain_run_id,
            url=TARGET_URL,
        )

        # End the chain with failure
        await handler.on_chain_error(
            error=Exception(f"Article scraping failed: {error_message}"),
            run_id=chain_run_id,
        )

        await handler.flush()

    print()
    print("=" * 60)
    print(" DEMO COMPLETE")
    print("=" * 60)
    print()
    print("What happened:")
    print("  1. Agent navigated to Medium article URL")
    print("  2. Medium showed partial content with paywall")
    print("  3. Agent tried to extract full article text")
    print("  4. Agent FAILED because paywall blocks full content")
    print()
    print("The Visual Mismatch:")
    print("  - Agent expected: Full article content")
    print("  - Screenshot shows: 'Member-only story' paywall")
    print("  - Gemini should say: 'Paywall blocking full article access'")
    print()
    print("Next steps:")
    print("  1. Open http://localhost:3000")
    print("  2. Select 'Paywall Demo - Medium Scraper' session")
    print("  3. Click DIAGNOSE on the error event")
    print()


if __name__ == "__main__":
    asyncio.run(main())
