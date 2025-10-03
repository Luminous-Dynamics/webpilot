"""
WebPilot Core - Modern Browser Automation

This module provides backward compatibility while transitioning to Playwright.
Import from here to automatically use the best available backend.
"""

from enum import Enum
from typing import Any, Dict

# Import Playwright implementations
from .playwright_automation import (
    PlaywrightAutomation,
    quick_screenshot,
    quick_page_text
)

from .webpilot_unified import (
    WebPilot,
    RealBrowserAutomation  # Backward compatibility alias
)

# Legacy stub classes for backward compatibility
# These were never fully implemented in the original codebase
class WebPilotSession:
    """Legacy stub - use PlaywrightAutomation or WebPilot instead."""
    def __init__(self, *args, **kwargs):
        raise NotImplementedError("WebPilotSession is deprecated. Use PlaywrightAutomation or WebPilot instead.")

class ActionResult:
    """Legacy stub for backward compatibility."""
    def __init__(self, success: bool, data: Any = None, error: str = None):
        self.success = success
        self.data = data
        self.error = error

class ActionType(Enum):
    """Legacy enum for backward compatibility."""
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    SCREENSHOT = "screenshot"

class BrowserType(Enum):
    """Browser types - maps to Playwright browser types."""
    FIREFOX = "firefox"
    CHROMIUM = "chromium"
    WEBKIT = "webkit"
    CHROME = "chromium"  # Alias

class WebElement:
    """Legacy stub for backward compatibility."""
    def __init__(self, selector: str, element: Any = None):
        self.selector = selector
        self.element = element

# Make all imports available at module level
__all__ = [
    # Playwright implementations
    'PlaywrightAutomation',
    'WebPilot',
    'RealBrowserAutomation',  # Legacy name points to Playwright now!
    'quick_screenshot',
    'quick_page_text',

    # Legacy stubs for backward compatibility
    'WebPilotSession',
    'ActionResult',
    'ActionType',
    'BrowserType',
    'WebElement',
]

# Version info
__version__ = '2.0.0-playwright'
__backend__ = 'playwright'

print(f"✨ WebPilot Core {__version__} loaded (backend: {__backend__})")
