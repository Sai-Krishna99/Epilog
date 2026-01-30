"""
Paywall Demo: Medium Article Scraper
====================================
This demo shows a real failure - Medium's paywall blocks full article access.

The agent navigates to a Medium article, captures a screenshot (showing paywall),
then actually tries to extract full content - which fails or returns partial content.

Usage:
    uv run python paywall_demo.py
"""

import asyncio
import uuid
from epilog.sdk import EpilogCallbackHandler, ScreenshotCapture


TARGET_URL = "https://medium.com/towards-data-science/yes-you-should-understand-backprop-e2f06eab496b"
ARTICLE_SELECTOR = "article p"


async def main():
    print("=" * 60)
    print(" PAYWALL DEMO")
    print("=" * 60)
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

        print(f"Session: {session_id}")
        print()

        chain_run_id = uuid.uuid4()

        # Start chain
        await handler.on_chain_start(
            serialized={"name": "MediumArticleScraper"},
            inputs={"task": "Extract full article content from Medium post"},
            run_id=chain_run_id,
        )

        # Navigate to article
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

        # Capture screenshot (may show paywall)
        await handler.on_tool_end_with_screenshot(
            output=f"Page loaded: {title}",
            run_id=nav_run_id,
            parent_run_id=chain_run_id,
            url=TARGET_URL,
        )
        print("Screenshot captured")

        # Try to extract article content
        extract_run_id = uuid.uuid4()
        await handler.on_tool_start(
            serialized={"name": "browser_extract"},
            input_str=f"Extract full article text from '{ARTICLE_SELECTOR}'",
            run_id=extract_run_id,
            parent_run_id=chain_run_id,
        )

        print(f"Extracting content with selector: {ARTICLE_SELECTOR}")

        # Actually try to extract
        try:
            element = await page.wait_for_selector(ARTICLE_SELECTOR, timeout=5000)
            if element:
                text = await element.text_content()
                await handler.on_tool_end(
                    output=f"Extracted: {text[:200]}...",
                    run_id=extract_run_id,
                    parent_run_id=chain_run_id,
                )
                print(f"Got content: {text[:100]}...")

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
