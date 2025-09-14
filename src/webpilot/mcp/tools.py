"""
MCP Tools definitions for WebPilot.

This module defines all the tools available through the MCP interface.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json


@dataclass
class ToolParameter:
    """Represents a tool parameter."""
    name: str
    type: str
    description: str
    required: bool = False
    default: Any = None
    enum: Optional[List[str]] = None


class WebPilotTools:
    """
    WebPilot tools available through MCP.
    
    This class defines all WebPilot capabilities as MCP tools.
    """
    
    @staticmethod
    def get_browser_control_tools() -> List[Dict[str, Any]]:
        """Get browser control tools."""
        return [
            {
                "name": "start_browser",
                "description": "Start a new browser session",
                "category": "browser_control",
                "parameters": [
                    ToolParameter("url", "string", "Initial URL to navigate to", required=True),
                    ToolParameter("browser", "string", "Browser type", default="firefox", 
                                enum=["firefox", "chrome", "chromium"]),
                    ToolParameter("headless", "boolean", "Run in headless mode", default=False)
                ]
            },
            {
                "name": "navigate",
                "description": "Navigate to a URL",
                "category": "browser_control",
                "parameters": [
                    ToolParameter("url", "string", "URL to navigate to", required=True)
                ]
            },
            {
                "name": "close_browser",
                "description": "Close the browser session",
                "category": "browser_control",
                "parameters": []
            },
            {
                "name": "refresh",
                "description": "Refresh the current page",
                "category": "browser_control",
                "parameters": []
            },
            {
                "name": "go_back",
                "description": "Go back in browser history",
                "category": "browser_control",
                "parameters": []
            },
            {
                "name": "go_forward",
                "description": "Go forward in browser history",
                "category": "browser_control",
                "parameters": []
            }
        ]
    
    @staticmethod
    def get_interaction_tools() -> List[Dict[str, Any]]:
        """Get page interaction tools."""
        return [
            {
                "name": "click",
                "description": "Click on an element",
                "category": "interaction",
                "parameters": [
                    ToolParameter("selector", "string", "CSS selector or XPath"),
                    ToolParameter("text", "string", "Text content of element"),
                    ToolParameter("x", "integer", "X coordinate"),
                    ToolParameter("y", "integer", "Y coordinate")
                ]
            },
            {
                "name": "type_text",
                "description": "Type text into an input field",
                "category": "interaction",
                "parameters": [
                    ToolParameter("text", "string", "Text to type", required=True),
                    ToolParameter("selector", "string", "Target element selector"),
                    ToolParameter("clear_first", "boolean", "Clear field before typing", default=False)
                ]
            },
            {
                "name": "select_option",
                "description": "Select an option from a dropdown",
                "category": "interaction",
                "parameters": [
                    ToolParameter("selector", "string", "Dropdown selector", required=True),
                    ToolParameter("value", "string", "Option value"),
                    ToolParameter("text", "string", "Option text"),
                    ToolParameter("index", "integer", "Option index")
                ]
            },
            {
                "name": "submit_form",
                "description": "Submit a form",
                "category": "interaction",
                "parameters": [
                    ToolParameter("selector", "string", "Form selector")
                ]
            },
            {
                "name": "scroll",
                "description": "Scroll the page",
                "category": "interaction",
                "parameters": [
                    ToolParameter("direction", "string", "Scroll direction", 
                                default="down", enum=["up", "down", "top", "bottom"]),
                    ToolParameter("amount", "integer", "Scroll amount", default=3)
                ]
            },
            {
                "name": "hover",
                "description": "Hover over an element",
                "category": "interaction",
                "parameters": [
                    ToolParameter("selector", "string", "Element selector", required=True)
                ]
            }
        ]
    
    @staticmethod
    def get_extraction_tools() -> List[Dict[str, Any]]:
        """Get data extraction tools."""
        return [
            {
                "name": "extract_text",
                "description": "Extract text from the page",
                "category": "extraction",
                "parameters": [
                    ToolParameter("selector", "string", "Element selector")
                ]
            },
            {
                "name": "extract_links",
                "description": "Extract all links from the page",
                "category": "extraction",
                "parameters": [
                    ToolParameter("filter", "string", "URL filter pattern")
                ]
            },
            {
                "name": "extract_images",
                "description": "Extract image URLs from the page",
                "category": "extraction",
                "parameters": [
                    ToolParameter("filter", "string", "Image URL filter")
                ]
            },
            {
                "name": "extract_table",
                "description": "Extract table data as JSON",
                "category": "extraction",
                "parameters": [
                    ToolParameter("selector", "string", "Table selector", required=True)
                ]
            },
            {
                "name": "get_page_source",
                "description": "Get the full page HTML source",
                "category": "extraction",
                "parameters": []
            }
        ]
    
    @staticmethod
    def get_validation_tools() -> List[Dict[str, Any]]:
        """Get validation and testing tools."""
        return [
            {
                "name": "check_element_exists",
                "description": "Check if an element exists on the page",
                "category": "validation",
                "parameters": [
                    ToolParameter("selector", "string", "Element selector", required=True)
                ]
            },
            {
                "name": "check_text_present",
                "description": "Check if text is present on the page",
                "category": "validation",
                "parameters": [
                    ToolParameter("text", "string", "Text to search for", required=True)
                ]
            },
            {
                "name": "wait_for_element",
                "description": "Wait for an element to appear",
                "category": "validation",
                "parameters": [
                    ToolParameter("selector", "string", "Element selector", required=True),
                    ToolParameter("timeout", "integer", "Timeout in seconds", default=10)
                ]
            },
            {
                "name": "check_accessibility",
                "description": "Run accessibility checks on the page",
                "category": "validation",
                "parameters": [
                    ToolParameter("standard", "string", "WCAG standard", 
                                default="WCAG2AA", enum=["WCAG2A", "WCAG2AA", "WCAG2AAA"])
                ]
            },
            {
                "name": "check_performance",
                "description": "Run performance analysis",
                "category": "validation",
                "parameters": []
            }
        ]
    
    @staticmethod
    def get_utility_tools() -> List[Dict[str, Any]]:
        """Get utility tools."""
        return [
            {
                "name": "take_screenshot",
                "description": "Take a screenshot of the page",
                "category": "utility",
                "parameters": [
                    ToolParameter("filename", "string", "Screenshot filename"),
                    ToolParameter("full_page", "boolean", "Capture full page", default=False)
                ]
            },
            {
                "name": "wait",
                "description": "Wait for a specified duration",
                "category": "utility",
                "parameters": [
                    ToolParameter("seconds", "number", "Seconds to wait", required=True)
                ]
            },
            {
                "name": "execute_javascript",
                "description": "Execute JavaScript code on the page",
                "category": "utility",
                "parameters": [
                    ToolParameter("code", "string", "JavaScript code to execute", required=True)
                ]
            },
            {
                "name": "set_viewport",
                "description": "Set browser viewport size",
                "category": "utility",
                "parameters": [
                    ToolParameter("width", "integer", "Viewport width", required=True),
                    ToolParameter("height", "integer", "Viewport height", required=True)
                ]
            },
            {
                "name": "clear_cookies",
                "description": "Clear browser cookies",
                "category": "utility",
                "parameters": []
            }
        ]
    
    @classmethod
    def get_all_tools(cls) -> List[Dict[str, Any]]:
        """Get all available tools."""
        all_tools = []
        all_tools.extend(cls.get_browser_control_tools())
        all_tools.extend(cls.get_interaction_tools())
        all_tools.extend(cls.get_extraction_tools())
        all_tools.extend(cls.get_validation_tools())
        all_tools.extend(cls.get_utility_tools())
        return all_tools
    
    @classmethod
    def get_tool_by_name(cls, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific tool by name."""
        for tool in cls.get_all_tools():
            if tool["name"] == name:
                return tool
        return None
    
    @classmethod
    def get_tools_by_category(cls, category: str) -> List[Dict[str, Any]]:
        """Get tools by category."""
        return [tool for tool in cls.get_all_tools() if tool.get("category") == category]