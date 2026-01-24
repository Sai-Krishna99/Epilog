"""Tests for screenshot and image compression utilities."""

import io
import pytest
from PIL import Image

from epilog.sdk.screenshot import ScreenshotCapture, compress_image


def test_compress_image():
    """Verify that images are correctly resized and converted to JPEG."""
    # Create a large red PNG in memory
    width, height = 2000, 1000
    img = Image.new("RGBA", (width, height), color="red")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    original_bytes = img_byte_arr.getvalue()
    
    # Compress it
    max_width = 800
    compressed_bytes = compress_image(original_bytes, max_width=max_width, quality=50)
    
    # Verify results
    assert len(compressed_bytes) < len(original_bytes)
    
    # Open compressed image and check dimensions
    compressed_img = Image.open(io.BytesIO(compressed_bytes))
    assert compressed_img.format == "JPEG"
    assert compressed_img.width == max_width
    # Height should maintain aspect ratio: 1000 * (800/2000) = 400
    assert compressed_img.height == 400


@pytest.mark.asyncio
async def test_screenshot_capture_url():
    """Verify that we can capture a real URL (requires playwright chromium)."""
    async with ScreenshotCapture(headless=True) as capture:
        # Using a reliable static site
        url = "https://example.com"
        screenshot_bytes = await capture.capture_url(url)
        
        assert isinstance(screenshot_bytes, bytes)
        assert len(screenshot_bytes) > 0
        
        # Verify it's a valid JPEG (from compress_image)
        img = Image.open(io.BytesIO(screenshot_bytes))
        assert img.format == "JPEG"
