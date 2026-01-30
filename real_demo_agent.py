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
    uv run python real_demo_agent.py
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
    print(" REAL DEMO: Hacker News Scraper")
    print("=" * 60)
    print()

    async with ScreenshotCapture(headless=True) as capture:
        handler = EpilogCallbackHandler(
            api_base_url="http://localhost:8000",
            session_name="Real Demo - HN Scraper (Wrong Selector)",
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
            serialized={"name": "HackerNewsScraper"},
            inputs={"task": "Extract the #1 headline from Hacker News"},
            run_id=chain_run_id,
        )

        # Navigate to HN
        nav_run_id = uuid.uuid4()
        await handler.on_tool_start(
            serialized={"name": "browser_navigate"},
            input_str="Navigate to https://news.ycombinator.com",
            run_id=nav_run_id,
            parent_run_id=chain_run_id,
        )

        print("Navigating to news.ycombinator.com...")

        # Create our own page for real navigation and extraction
        page = await capture._browser.new_page(
            viewport={"width": 1280, "height": 720}
        )

        try:
            await page.goto("https://news.ycombinator.com", wait_until="load", timeout=30000)
            title = await page.title()
            print(f"Page loaded: {title}")

            # Capture screenshot
            await handler.on_tool_end_with_screenshot(
                output=f"Page loaded: {title}",
                run_id=nav_run_id,
                parent_run_id=chain_run_id,
                page=page,
            )
            print("Screenshot captured")

            # Try to extract with WRONG selector
            extract_run_id = uuid.uuid4()
            await handler.on_tool_start(
                serialized={"name": "browser_extract"},
                input_str=f"Extract text from element matching '{WRONG_SELECTOR}'",
                run_id=extract_run_id,
                parent_run_id=chain_run_id,
            )

            print(f"Extracting headline with selector: {WRONG_SELECTOR}")

            # Actually try to extract - this will fail because selector is wrong
            try:
                element = await page.wait_for_selector(WRONG_SELECTOR, timeout=5000)
                if element:
                    text = await element.text_content()
                    await handler.on_tool_end(
                        output=f"Headline: {text}",
                        run_id=extract_run_id,
                        parent_run_id=chain_run_id,
                    )
                    print(f"Success: {text}")

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
                    page=page,
                )

                await handler.on_chain_error(
                    error=e,
                    run_id=chain_run_id,
                )

        finally:
            await page.close()

        await handler.flush()

    print()
    print("Done. Check http://localhost:3000 for the session.")
    print()
    print(f"Note: Agent used outdated selector '{WRONG_SELECTOR}'")
    print(f"      Current HN uses '{CORRECT_SELECTOR}'")
    print()


if __name__ == "__main__":
    asyncio.run(main())
