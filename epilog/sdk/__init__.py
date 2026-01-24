"""Epilog SDK for agent observability."""

from epilog.sdk.callback_handler import EpilogCallbackHandler
from epilog.sdk.client import EpilogClient
from epilog.sdk.screenshot import ScreenshotCapture, compress_image

__all__ = ["EpilogCallbackHandler", "EpilogClient", "ScreenshotCapture", "compress_image"]
