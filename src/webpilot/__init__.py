"""
WebPilot - Comprehensive Web Automation and DevOps Testing Framework
Now with Model Context Protocol (MCP) support for AI assistant integration.
"""

__version__ = "1.1.0"

# Core imports
from .core import (
    WebPilot,
    WebPilotSession,
    ActionResult,
    ActionType,
    BrowserType,
    WebElement
)

# Backends
from .backends.selenium import SeleniumWebPilot
from .backends.async_pilot import AsyncWebPilot

# Features
from .features.vision import WebPilotVision
from .features.devops import (
    WebPilotDevOps,
    PerformanceMetrics,
    AccessibilityReport
)

# Integrations
from .integrations.cicd import WebPilotCICD

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
    # Core
    'WebPilot',
    'WebPilotSession',
    'ActionResult',
    'ActionType',
    'BrowserType',
    'WebElement',
    
    # Backends
    'SeleniumWebPilot',
    'AsyncWebPilot',
    
    # Features
    'WebPilotVision',
    'WebPilotDevOps',
    'PerformanceMetrics',
    'AccessibilityReport',
    
    # Integrations
    'WebPilotCICD',
    
    # MCP components
    'WebPilotMCPServer',
    'WebPilotTools',
    'WebPilotResources',
    'MCP_AVAILABLE',
]