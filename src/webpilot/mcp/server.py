"""
MCP Server implementation for WebPilot.

This provides a Model Context Protocol server that exposes WebPilot
functionality to AI assistants like Claude.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import logging

from ..core import WebPilot, ActionResult
from ..utils.logging_config import get_logger
from .resources import WebPilotResources, SessionResource

logger = get_logger(__name__)


@dataclass
class MCPTool:
    """Represents an MCP tool definition."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to MCP tool format."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema
        }


@dataclass
class MCPResource:
    """Represents an MCP resource."""
    uri: str
    name: str
    description: str
    mime_type: str = "application/json"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to MCP resource format."""
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
            "mimeType": self.mime_type
        }


class WebPilotMCPServer:
    """
    MCP Server for WebPilot web automation.
    
    This server exposes WebPilot functionality through the Model Context Protocol,
    allowing AI assistants to perform web automation tasks.
    """
    
    def __init__(self):
        """Initialize the MCP server."""
        self.pilot: Optional[WebPilot] = None
        self.sessions: Dict[str, WebPilot] = {}
        self.logger = get_logger(__name__)
        self.resources = WebPilotResources()
        
    def get_tools(self) -> List[MCPTool]:
        """
        Get available MCP tools.
        
        Returns:
            List of available tools for web automation
        """
        return [
            MCPTool(
                name="webpilot_start",
                description="Start a browser session and navigate to a URL",
                input_schema={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL to navigate to"
                        },
                        "browser": {
                            "type": "string",
                            "enum": ["firefox", "chrome", "chromium"],
                            "default": "firefox",
                            "description": "Browser to use"
                        },
                        "headless": {
                            "type": "boolean",
                            "default": False,
                            "description": "Run in headless mode"
                        }
                    },
                    "required": ["url"]
                }
            ),
            MCPTool(
                name="webpilot_navigate",
                description="Navigate to a URL in the current session",
                input_schema={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL to navigate to"
                        }
                    },
                    "required": ["url"]
                }
            ),
            MCPTool(
                name="webpilot_click",
                description="Click on an element",
                input_schema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text of the element to click"
                        },
                        "selector": {
                            "type": "string",
                            "description": "CSS selector of the element"
                        },
                        "x": {
                            "type": "integer",
                            "description": "X coordinate to click"
                        },
                        "y": {
                            "type": "integer",
                            "description": "Y coordinate to click"
                        }
                    }
                }
            ),
            MCPTool(
                name="webpilot_type",
                description="Type text into the focused element",
                input_schema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to type"
                        },
                        "clear_first": {
                            "type": "boolean",
                            "default": False,
                            "description": "Clear the field before typing"
                        }
                    },
                    "required": ["text"]
                }
            ),
            MCPTool(
                name="webpilot_screenshot",
                description="Take a screenshot of the current page",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name for the screenshot file"
                        }
                    }
                }
            ),
            MCPTool(
                name="webpilot_extract",
                description="Extract content from the current page",
                input_schema={
                    "type": "object",
                    "properties": {}
                }
            ),
            MCPTool(
                name="webpilot_scroll",
                description="Scroll the page",
                input_schema={
                    "type": "object",
                    "properties": {
                        "direction": {
                            "type": "string",
                            "enum": ["up", "down", "top", "bottom"],
                            "default": "down",
                            "description": "Scroll direction"
                        },
                        "amount": {
                            "type": "integer",
                            "default": 3,
                            "description": "Amount to scroll"
                        }
                    }
                }
            ),
            MCPTool(
                name="webpilot_close",
                description="Close the browser session",
                input_schema={
                    "type": "object",
                    "properties": {}
                }
            ),
            MCPTool(
                name="webpilot_wait",
                description="Wait for a specified number of seconds",
                input_schema={
                    "type": "object",
                    "properties": {
                        "seconds": {
                            "type": "number",
                            "description": "Number of seconds to wait"
                        }
                    },
                    "required": ["seconds"]
                }
            )
        ]
    
    def get_resources(self) -> List[MCPResource]:
        """
        Get available MCP resources.
        
        Returns:
            List of available resources
        """
        # Get resources from the resources manager
        mcp_resources = self.resources.get_all_resources()
        
        # Convert to MCPResource objects
        resources = []
        for resource_dict in mcp_resources:
            resources.append(MCPResource(
                uri=resource_dict["uri"],
                name=resource_dict["name"],
                description=resource_dict["description"],
                mime_type=resource_dict["mimeType"]
            ))
        
        return resources
    
    async def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an MCP tool call.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        try:
            if tool_name == "webpilot_start":
                # Create new WebPilot instance
                from webpilot.core import BrowserType
                browser_type = BrowserType[arguments.get('browser', 'firefox').upper()]
                self.pilot = WebPilot(
                    browser=browser_type,
                    headless=arguments.get('headless', False)
                )
                result = self.pilot.start(arguments['url'])
                session_id = self.pilot.session.session_id
                self.sessions[session_id] = self.pilot
                
                # Create session resource
                session_resource = self.resources.create_session(session_id)
                session_resource.current_url = arguments['url']
                
                # Log action
                self.resources.add_action(session_id, "start", url=arguments['url'])
                
                return {
                    "success": result.success,
                    "session_id": session_id,
                    "data": result.data,
                    "error": result.error
                }
            
            # All other tools require an active session
            if not self.pilot:
                return {
                    "success": False,
                    "error": "No active session. Use webpilot_start first."
                }
            
            if tool_name == "webpilot_navigate":
                result = self.pilot.navigate(arguments['url'])
            elif tool_name == "webpilot_click":
                result = self.pilot.click(
                    x=arguments.get('x'),
                    y=arguments.get('y'),
                    text=arguments.get('text'),
                    selector=arguments.get('selector')
                )
            elif tool_name == "webpilot_type":
                result = self.pilot.type_text(
                    arguments['text'],
                    clear_first=arguments.get('clear_first', False)
                )
            elif tool_name == "webpilot_screenshot":
                result = self.pilot.screenshot(arguments.get('name'))
            elif tool_name == "webpilot_extract":
                result = self.pilot.extract_page_content()
            elif tool_name == "webpilot_scroll":
                result = self.pilot.scroll(
                    direction=arguments.get('direction', 'down'),
                    amount=arguments.get('amount', 3)
                )
            elif tool_name == "webpilot_wait":
                result = self.pilot.wait(arguments['seconds'])
            elif tool_name == "webpilot_close":
                result = self.pilot.close()
                self.pilot = None
            else:
                return {
                    "success": False,
                    "error": f"Unknown tool: {tool_name}"
                }
            
            return {
                "success": result.success,
                "data": result.data,
                "error": result.error,
                "duration_ms": result.duration_ms
            }
            
        except Exception as e:
            self.logger.error(f"Tool execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def handle_resource_read(self, uri: str) -> Dict[str, Any]:
        """
        Handle an MCP resource read request.
        
        Args:
            uri: Resource URI to read
            
        Returns:
            Resource content
        """
        try:
            resource = self.resources.get_resource_by_uri(uri)
            if resource:
                return {
                    "success": True,
                    "content": resource.get("content", {})
                }
            
            return {
                "success": False,
                "error": f"Resource not found: {uri}"
            }
            
        except Exception as e:
            self.logger.error(f"Resource read failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_server_info(self) -> Dict[str, Any]:
        """
        Get MCP server information.
        
        Returns:
            Server metadata
        """
        return {
            "name": "webpilot-mcp",
            "version": "1.1.0",
            "description": "WebPilot MCP server for web automation",
            "capabilities": {
                "tools": True,
                "resources": True,
                "prompts": False,
                "sampling": False
            }
        }


# Example MCP server runner
async def run_mcp_server():
    """Run the WebPilot MCP server."""
    server = WebPilotMCPServer()
    
    # This would typically connect to an MCP client
    # For now, just demonstrate the interface
    print("WebPilot MCP Server Started")
    print(f"Server Info: {json.dumps(server.get_server_info(), indent=2)}")
    print(f"Available Tools: {len(server.get_tools())}")
    
    # Keep server running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("Server stopped")


if __name__ == "__main__":
    asyncio.run(run_mcp_server())