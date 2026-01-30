"""
Login Wall Demo: LinkedIn Profile Scraper
==========================================
This demo shows a real failure - LinkedIn's login wall blocks profile access.

The agent navigates to a LinkedIn profile, captures a screenshot (showing login wall),
then actually tries to extract profile data - which fails because auth is required.

WARNING: LinkedIn may rate-limit repeated requests. Use sparingly.

Usage:
    uv run python login_wall_demo.py
"""

import asyncio
import uuid
from epilog.sdk import EpilogCallbackHandler, ScreenshotCapture


TARGET_URL = "https://www.linkedin.com/in/sundarpichai/"
PROFILE_NAME_SELECTOR = ".text-heading-xlarge"


async def main():
    print("=" * 60)
    print(" LOGIN WALL DEMO")
    print("=" * 60)
    print()
    print("WARNING: LinkedIn may rate-limit. Use sparingly.")
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
            print("Make sure the API is running.")
            return

        print(f"Session: {session_id}")
        print()

        chain_run_id = uuid.uuid4()

        # Start chain
        await handler.on_chain_start(
            serialized={"name": "LinkedInProfileScraper"},
            inputs={"task": "Extract name and job title from LinkedIn profile"},
            run_id=chain_run_id,
        )

        # Navigate to profile
        nav_run_id = uuid.uuid4()
        await handler.on_tool_start(
            serialized={"name": "browser_navigate"},
            input_str=f"Navigate to {TARGET_URL}",
            run_id=nav_run_id,
            parent_run_id=chain_run_id,
        )

        print(f"Navigating to {TARGET_URL}...")

        # Create our own page for real navigation and extraction
        page = await capture._browser.new_page(
            viewport={"width": 1280, "height": 720}
        )

        try:
            await page.goto(TARGET_URL, wait_until="load", timeout=30000)
            title = await page.title()
            print(f"Page loaded: {title}")

            # Capture screenshot (will show login wall)
            await handler.on_tool_end_with_screenshot(
                output=f"Page loaded: {title}",
                run_id=nav_run_id,
                parent_run_id=chain_run_id,
                page=page,
            )
            print("Screenshot captured")

            # Try to extract profile name
            extract_run_id = uuid.uuid4()
            await handler.on_tool_start(
                serialized={"name": "browser_extract"},
                input_str=f"Extract profile name from '{PROFILE_NAME_SELECTOR}'",
                run_id=extract_run_id,
                parent_run_id=chain_run_id,
            )

            print(f"Extracting profile name with selector: {PROFILE_NAME_SELECTOR}")

            # Actually try to extract - this will fail if login wall blocks content
            try:
                element = await page.wait_for_selector(PROFILE_NAME_SELECTOR, timeout=5000)
                if element:
                    text = await element.text_content()
                    await handler.on_tool_end(
                        output=f"Profile name: {text}",
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


if __name__ == "__main__":
    asyncio.run(main())
