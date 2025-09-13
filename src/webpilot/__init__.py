"""
WebPilot - Comprehensive Web Automation and DevOps Testing Framework
"""

__version__ = "1.0.0"

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
]