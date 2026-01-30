"""
Before Epilog: What Debugging Looks Like Today
==============================================
This runs the same browser automation WITHOUT Epilog.
You only see terminal errors - no visual context.

Run this FIRST to show the "before" state,
then run cookie_popup_demo.py to show "after" with Epilog.
"""

import asyncio
from playwright.async_api import async_playwright

TARGET_URL = "https://www.theguardian.com/technology"
ARTICLE_SELECTOR = ".dcr-1ay7pd6"


async def main():
    print()
    print("=" * 60)
    print(" WITHOUT EPILOG: Browser Automation Debugging")
    print("=" * 60)
    print()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print(f"Navigating to {TARGET_URL}...")
        await page.goto(TARGET_URL, wait_until="load", timeout=30000)

        title = await page.title()
        print(f"Page loaded: {title}")
        print()

        print(f"Extracting content with selector: {ARTICLE_SELECTOR}")
        try:
            element = await page.wait_for_selector(ARTICLE_SELECTOR, timeout=5000)
            if element:
                text = await element.text_content()
                print(f"Success: {text[:100]}...")
        except Exception as e:
            print()
            print("ERROR: " + str(e))
            print()

            # Try alternate selector
            print("Trying alternate selector: article h3")
            try:
                element = await page.wait_for_selector("article h3", timeout=5000)
                if element:
                    text = await element.text_content()
                    print(f"Success: {text[:100]}...")
            except Exception as e2:
                print("ERROR: " + str(e2))

        await browser.close()

    print()
    print("=" * 60)
    print(" THE PROBLEM")
    print("=" * 60)
    print()
    print("The page loaded. The selectors failed. But WHY?")
    print()
    print("You don't know if it was:")
    print("  - A cookie popup blocking content")
    print("  - A layout change")
    print("  - A login wall")
    print("  - Something else entirely")
    print()
    print("To find out, you have to manually open a browser and check.")
    print()
    print("=" * 60)
    print(" NOW RUN: uv run python cookie_popup_demo.py")
    print("=" * 60)
    print()
    print("See how Epilog captures a screenshot that shows exactly")
    print("what blocked the content - no manual investigation needed.")
    print()


if __name__ == "__main__":
    asyncio.run(main())
