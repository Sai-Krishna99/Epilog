"""Screenshot capture and image processing utilities."""

import io
import logging
from typing import Any, Optional, Union

try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

try:
    from playwright.async_api import Page, async_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

logger = logging.getLogger("epilog.sdk.screenshot")


def compress_image(
    image_bytes: bytes, 
    max_width: int = 1280, 
    quality: int = 80
) -> bytes:
    """Resize and compress an image to JPEG to save bandwidth and tokens.

    Args:
        image_bytes: Original image bytes (e.g., PNG)
        max_width: Maximum width for the resized image
        quality: JPEG compression quality (1-95)

    Returns:
        Compressed JPEG bytes
    """
    if not HAS_PILLOW:
        logger.warning("Pillow not installed, skipping image compression")
        return image_bytes

    try:
        img = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if necessary (e.g., for PNG with alpha)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # Resize if wider than max_width
        if img.width > max_width:
            ratio = max_width / float(img.width)
            new_height = int(float(img.height) * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

        # Save to JPEG bytes
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=quality, optimize=True)
        return output.getvalue()
    except Exception as e:
        logger.error(f"Failed to compress image: {e}")
        return image_bytes


class ScreenshotCapture:
    """Optional helper for capturing screenshots via Playwright."""

    def __init__(
        self, 
        headless: bool = True, 
        viewport_width: int = 1280, 
        viewport_height: int = 720
    ):
        """Initialize ScreenshotCapture.

        Args:
            headless: Whether to run the browser headlessly
            viewport_width: Width of the browser viewport
            viewport_height: Height of the browser viewport
        """
        self.headless = headless
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self._playwright = None
        self._browser = None

    async def __aenter__(self):
        if not HAS_PLAYWRIGHT:
            raise ImportError(
                "Playwright is not installed. Please install it with 'pip install playwright' "
                "and run 'playwright install chromium'."
            )
        
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def capture_url(
        self, 
        url: str, 
        wait_until: str = "networkidle", 
        full_page: bool = False
    ) -> bytes:
        """Navigate to a URL and capture a compressed screenshot.

        Args:
            url: The URL to capture
            wait_until: Playwright wait strategy
            full_page: Whether to capture the full scrolling page

        Returns:
            Compressed JPEG screenshot bytes
        """
        if not self._browser:
            # Context manager not used, we probably shouldn't auto-start here 
            # to be explicit about lifecycle, but for MVP let's warn.
            raise RuntimeError("ScreenshotCapture must be used as an async context manager")

        page = await self._browser.new_page(
            viewport={"width": self.viewport_width, "height": self.viewport_height}
        )
        try:
            await page.goto(url, wait_until=wait_until)
            screenshot_bytes = await page.screenshot(full_page=full_page)
            return compress_image(screenshot_bytes)
        finally:
            await page.close()

    async def capture_page(self, page: Any, full_page: bool = False) -> bytes:
        """Capture a compressed screenshot from an existing Playwright Page object.

        Args:
            page: A Playwright Page object
            full_page: Whether to capture the full scrolling page

        Returns:
            Compressed JPEG screenshot bytes
        """
        screenshot_bytes = await page.screenshot(full_page=full_page)
        return compress_image(screenshot_bytes)
