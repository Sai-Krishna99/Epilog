"""
Cookie Popup Demo: News Scraper
===============================
This demo shows a real failure - a cookie consent modal blocks content extraction.

The agent navigates to The Guardian, captures a screenshot (showing the cookie modal),
then actually tries to extract article content - which fails because the modal blocks it.

Usage:
    uv run python cookie_popup_demo.py
"""

import asyncio
import uuid
from epilog.sdk import EpilogCallbackHandler, ScreenshotCapture


TARGET_URL = "https://www.theguardian.com/world"
ARTICLE_SELECTOR = ".dcr-1ay6c8e"


async def main():
    print("=" * 60)
    print(" COOKIE POPUP DEMO")
    print("=" * 60)
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
            print("Make sure the API is running.")
            return

        print(f"Session: {session_id}")
        print()

        chain_run_id = uuid.uuid4()

        # Start chain
        await handler.on_chain_start(
            serialized={"name": "NewsArticleScraper"},
            inputs={"task": "Extract top news headlines from The Guardian"},
            run_id=chain_run_id,
        )

        # Navigate to page
        nav_run_id = uuid.uuid4()
        await handler.on_tool_start(
            serialized={"name": "browser_navigate"},
            input_str=f"Navigate to {TARGET_URL}",
            run_id=nav_run_id,
            parent_run_id=chain_run_id,
        )

        print(f"Navigating to {TARGET_URL}...")

        # Actually navigate and capture screenshot
        page = capture._page
        await page.goto(TARGET_URL, wait_until="load", timeout=30000)
        title = await page.title()
        print(f"Page loaded: {title}")

        # Capture screenshot (will show cookie modal)
        await handler.on_tool_end_with_screenshot(
            output=f"Page loaded: {title}",
            run_id=nav_run_id,
            parent_run_id=chain_run_id,
            url=TARGET_URL,
        )
        print("Screenshot captured")

        # Try to extract content
        extract_run_id = uuid.uuid4()
        await handler.on_tool_start(
            serialized={"name": "browser_extract"},
            input_str=f"Extract text from elements matching '{ARTICLE_SELECTOR}'",
            run_id=extract_run_id,
            parent_run_id=chain_run_id,
        )

        print(f"Extracting content with selector: {ARTICLE_SELECTOR}")

        # Actually try to extract - this will fail if cookie modal blocks content
        try:
            element = await page.wait_for_selector(ARTICLE_SELECTOR, timeout=5000)
            if element:
                text = await element.text_content()
                await handler.on_tool_end(
                    output=f"Extracted: {text[:200]}...",
                    run_id=extract_run_id,
                    parent_run_id=chain_run_id,
                )
                print(f"Success: {text[:100]}...")

                await handler.on_chain_end(
                    outputs={"result": text},
                    run_id=chain_run_id,
                )
        except Exception as e:
            # Real error from real attempt
            print(f"ERROR: {e}")

            await handler.on_tool_error(
                error=e,
                run_id=extract_run_id,
                parent_run_id=chain_run_id,
            )

            # Capture screenshot at failure
            screenshot_run_id = uuid.uuid4()
            await handler.on_tool_end_with_screenshot(
                output=f"Extraction failed: {e}",
                run_id=screenshot_run_id,
                parent_run_id=chain_run_id,
                url=TARGET_URL,
            )

            await handler.on_chain_error(
                error=e,
                run_id=chain_run_id,
            )

        await handler.flush()

    print()
    print("Done. Check http://localhost:3000 for the session.")
    print()


if __name__ == "__main__":
    asyncio.run(main())
