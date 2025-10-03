"""
WebPilot v2.0 - AI Orchestration Layer for Playwright
"""

from .ai_webpilot import AIWebPilot, WebPilotConfig
from .playwright_adapter import PlaywrightAdapter

__version__ = "2.0.0-alpha"

__all__ = [
    "AIWebPilot",
    "WebPilotConfig",
    "PlaywrightAdapter",
]