"""
Model Context Protocol (MCP) integration for WebPilot.

This module provides MCP server capabilities for WebPilot, allowing
AI assistants to control web automation through standardized protocols.
"""

from .server import WebPilotMCPServer
from .tools import WebPilotTools
from .resources import WebPilotResources

__all__ = ['WebPilotMCPServer', 'WebPilotTools', 'WebPilotResources']