"""
WebPilot - Comprehensive Web Automation and DevOps Testing Framework
Now powered by Playwright for superior performance and reliability.
"""

__version__ = "2.0.0-playwright"

# Core Playwright implementations
from .core import (
    WebPilot,
    PlaywrightAutomation,
    RealBrowserAutomation,
    # Legacy stubs for backward compatibility
    WebPilotSession,
    ActionResult,
    ActionType,
    BrowserType,
    WebElement
)

# Optional features - import only if available
try:
    from .backends.selenium import SeleniumWebPilot
except ImportError:
    SeleniumWebPilot = None

try:
    from .backends.async_pilot import AsyncWebPilot
except ImportError:
    AsyncWebPilot = None

try:
    from .features.vision import WebPilotVision
except ImportError:
    WebPilotVision = None

try:
    from .features.devops import (
        WebPilotDevOps,
        PerformanceMetrics,
        AccessibilityReport
    )
except ImportError:
    WebPilotDevOps = None
    PerformanceMetrics = None
    AccessibilityReport = None

try:
    from .integrations.cicd import WebPilotCICD
except ImportError:
    WebPilotCICD = None

# MCP Support
try:
    from .mcp import WebPilotMCPServer, WebPilotTools, WebPilotResources
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    WebPilotMCPServer = None
    WebPilotTools = None
    WebPilotResources = None

# Convenience imports
__all__ = [
    # Core Playwright
    'WebPilot',
    'PlaywrightAutomation',
    'RealBrowserAutomation',

    # Legacy compatibility
    'WebPilotSession',
    'ActionResult',
    'ActionType',
    'BrowserType',
    'WebElement',

    # Optional backends
    'SeleniumWebPilot',
    'AsyncWebPilot',

    # Optional features
    'WebPilotVision',
    'WebPilotDevOps',
    'PerformanceMetrics',
    'AccessibilityReport',

    # Optional integrations
    'WebPilotCICD',

    # MCP components
    'WebPilotMCPServer',
    'WebPilotTools',
    'WebPilotResources',
    'MCP_AVAILABLE',
]