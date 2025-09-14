"""
MCP Server implementation for WebPilot.

This provides a Model Context Protocol server that exposes WebPilot
functionality to AI assistants like Claude.
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import logging

from ..core import WebPilot, ActionResult
from ..utils.logging_config import get_logger
from .resources import WebPilotResources, SessionResource
from .tools import WebPilotTools
from .tools_extended import WebPilotExtendedTools
from .error_handler import error_handler
from .cloud_manager import cloud_manager, CloudPlatform, CloudCapabilities
from .performance import performance_optimizer

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
        Handle an MCP tool call with intelligent error handling.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            
        Returns:
            Tool execution result with error recovery suggestions
        """
        context = {
            "tool": tool_name,
            "arguments": arguments,
            "session_active": self.pilot is not None
        }
        
        try:
            if tool_name == "webpilot_start":
                # Create new WebPilot instance
                from webpilot.core import BrowserType
                browser_type = BrowserType[arguments.get('browser', 'firefox').upper()]
                context["browser"] = browser_type.value
                context["url"] = arguments.get('url')
                context["headless"] = arguments.get('headless', False)
                
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
                return error_handler.handle_error(
                    ValueError("No active session. Use webpilot_start first."),
                    context
                )
            
            # Add current URL to context
            if hasattr(self.pilot, 'current_url'):
                context["url"] = self.pilot.current_url
            
            # Handle extended tools
            if tool_name.startswith("webpilot_") and not hasattr(self, f"_handle_{tool_name}"):
                return await self._handle_extended_tool(tool_name, arguments, context)
            
            # Handle basic tools
            if tool_name == "webpilot_navigate":
                context["url"] = arguments.get('url')
                result = self.pilot.navigate(arguments['url'])
            elif tool_name == "webpilot_click":
                context["selector"] = arguments.get('selector') or arguments.get('text')
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
                return error_handler.handle_error(
                    ValueError(f"Unknown tool: {tool_name}"),
                    context
                )
            
            return {
                "success": result.success,
                "data": result.data,
                "error": result.error,
                "duration_ms": result.duration_ms
            }
            
        except Exception as e:
            # Use intelligent error handler
            return error_handler.handle_error(e, context)
    
    async def _handle_extended_tool(self, tool_name: str, arguments: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle extended tools dynamically.
        
        Args:
            tool_name: Name of the extended tool
            arguments: Tool arguments
            context: Error context
            
        Returns:
            Tool execution result
        """
        # Strip the webpilot_ prefix
        tool_base_name = tool_name.replace("webpilot_", "")
        
        # Map extended tool names to pilot methods
        extended_mappings = {
            # Form tools
            "fill_form_auto": lambda args: self.pilot.fill_form_auto(
                args.get('form_selector'), args.get('use_faker', True)
            ),
            "upload_file": lambda args: self.pilot.upload_file(
                args['selector'], args['file_path']
            ),
            "validate_form": lambda args: self.pilot.validate_form(
                args.get('form_selector')
            ),
            "clear_form": lambda args: self.pilot.clear_form(
                args.get('form_selector')
            ),
            
            # Navigation tools
            "open_new_tab": lambda args: self.pilot.open_new_tab(args['url']),
            "switch_tab": lambda args: self.pilot.switch_tab(
                index=args.get('index'), title=args.get('title')
            ),
            "close_tab": lambda args: self.pilot.close_tab(args.get('index')),
            "handle_alert": lambda args: self.pilot.handle_alert(args.get('action', 'read')),
            
            # Data extraction tools
            "extract_structured_data": lambda args: self.pilot.extract_structured_data(
                args['schema']
            ),
            "extract_json_ld": lambda args: self.pilot.extract_json_ld(),
            "extract_meta_tags": lambda args: self.pilot.extract_meta_tags(),
            "extract_emails": lambda args: self.pilot.extract_emails(
                unique=args.get('unique', True)
            ),
            "save_as_pdf": lambda args: self.pilot.save_as_pdf(
                args.get('filename', 'page.pdf')
            ),
            
            # Testing tools
            "check_broken_links": lambda args: self.pilot.check_broken_links(
                check_external=args.get('check_external', False)
            ),
            "check_console_errors": lambda args: self.pilot.check_console_errors(),
            "measure_load_time": lambda args: self.pilot.measure_load_time(),
            
            # Interaction tools
            "drag_and_drop": lambda args: self.pilot.drag_and_drop(
                args['source'], args['target']
            ),
            "right_click": lambda args: self.pilot.right_click(args['selector']),
            "double_click": lambda args: self.pilot.double_click(args['selector']),
            "press_key": lambda args: self.pilot.press_key(
                args['key'], modifiers=args.get('modifiers', [])
            ),
            
            # Automation tools
            "login": lambda args: self.pilot.login(
                args['username'], args['password'], 
                auto_detect=args.get('auto_detect', True)
            ),
            "search_and_filter": lambda args: self.pilot.search_and_filter(
                args['query'], filters=args.get('filters')
            ),
            "monitor_changes": lambda args: self.pilot.monitor_changes(
                selector=args.get('selector'),
                interval=args.get('interval', 5),
                timeout=args.get('timeout', 60)
            ),
            
            # Cloud platform tools
            "browserstack_session": lambda args: self._handle_cloud_session(
                CloudPlatform.BROWSERSTACK, args
            ),
            "sauce_labs_session": lambda args: self._handle_cloud_session(
                CloudPlatform.SAUCE_LABS, args
            ),
            "lambda_test_session": lambda args: self._handle_cloud_session(
                CloudPlatform.LAMBDA_TEST, args
            )
        }
        
        # Check if we have a handler for this tool
        if tool_base_name in extended_mappings:
            try:
                # Call the appropriate method
                handler = extended_mappings[tool_base_name]
                result = handler(arguments)
                
                # Convert result to standard format if needed
                if hasattr(result, 'success'):
                    return {
                        "success": result.success,
                        "data": result.data,
                        "error": result.error,
                        "duration_ms": getattr(result, 'duration_ms', None)
                    }
                else:
                    # Assume success if we got a result
                    return {
                        "success": True,
                        "data": result,
                        "error": None
                    }
                    
            except AttributeError as e:
                # Method doesn't exist on pilot - provide helpful error
                return error_handler.handle_error(
                    NotImplementedError(f"Extended tool '{tool_base_name}' not yet implemented in core WebPilot"),
                    context
                )
            except Exception as e:
                return error_handler.handle_error(e, context)
        else:
            return error_handler.handle_error(
                ValueError(f"Unknown extended tool: {tool_name}"),
                context
            )
    
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
    
    def get_extended_tools(self) -> List[MCPTool]:
        """
        Get extended MCP tools from tools_extended module.
        
        Returns:
            List of extended tools
        """
        extended_tools = []
        
        # Get all extended tools
        for tool_dict in WebPilotExtendedTools.get_all_extended_tools():
            # Convert to MCPTool format
            input_schema = {
                "type": "object",
                "properties": {},
                "required": []
            }
            
            # Process parameters
            for param in tool_dict.get("parameters", []):
                prop = {
                    "type": param.type,
                    "description": param.description
                }
                if param.default is not None:
                    prop["default"] = param.default
                if param.enum:
                    prop["enum"] = param.enum
                    
                input_schema["properties"][param.name] = prop
                if param.required:
                    input_schema["required"].append(param.name)
            
            extended_tools.append(MCPTool(
                name=f"webpilot_{tool_dict['name']}",
                description=tool_dict['description'],
                input_schema=input_schema
            ))
        
        return extended_tools
    
    def get_all_tools(self) -> List[MCPTool]:
        """
        Get all available tools (basic + extended).
        
        Returns:
            Complete list of MCP tools
        """
        all_tools = self.get_tools()  # Basic tools
        all_tools.extend(self.get_extended_tools())  # Extended tools
        return all_tools
    
    def _handle_cloud_session(self, platform: CloudPlatform, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle cloud platform session creation.
        
        Args:
            platform: Cloud platform to use
            args: Session arguments
            
        Returns:
            Session creation result
        """
        capabilities = CloudCapabilities(
            browser=args.get('browser', 'chrome'),
            browser_version=args.get('browser_version'),
            os=args.get('os'),
            os_version=args.get('os_version'),
            resolution=args.get('resolution'),
            device=args.get('device'),
            real_mobile=args.get('real_mobile', False),
            local_testing=args.get('local_testing', False),
            video=args.get('video', True),
            console_logs=args.get('console_logs', True),
            network_logs=args.get('network_logs', False),
            visual_testing=args.get('visual_testing', False)
        )
        
        session_name = args.get('build_name') or args.get('test_name')
        
        return cloud_manager.create_session(
            platform=platform,
            capabilities=capabilities,
            session_name=session_name
        )
    
    async def handle_tool_call_with_performance(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle tool call with performance tracking.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            
        Returns:
            Tool execution result with performance metrics
        """
        # Check cache first
        cached_result = performance_optimizer.cache.get(tool_name, arguments)
        if cached_result is not None:
            cached_result["cache_hit"] = True
            return cached_result
        
        # Execute with performance tracking
        start_time = time.time()
        result = await self.handle_tool_call(tool_name, arguments)
        duration_ms = (time.time() - start_time) * 1000
        
        # Add performance metrics
        result["performance"] = {
            "duration_ms": duration_ms,
            "cache_hit": False
        }
        
        # Cache successful results
        if result.get("success"):
            performance_optimizer.cache.set(tool_name, arguments, result)
        
        # Track metrics
        from .performance import PerformanceMetrics
        metric = PerformanceMetrics(
            operation=tool_name,
            start_time=start_time,
            end_time=time.time(),
            duration_ms=duration_ms,
            success=result.get("success", False),
            cache_hit=False,
            error=result.get("error")
        )
        performance_optimizer.metrics.append(metric)
        
        return result
    
    async def batch_execute_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute multiple tools in batch with optimization.
        
        Args:
            tools: List of tool calls to execute
            
        Returns:
            List of results
        """
        return await performance_optimizer.batch_execute(tools)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        return performance_optimizer.get_performance_stats()
    
    def optimize_for_scenario(self, scenario: str) -> Dict[str, Any]:
        """
        Optimize MCP server for specific scenario.
        
        Args:
            scenario: One of 'speed', 'accuracy', 'balanced', 'batch'
            
        Returns:
            Optimization result
        """
        performance_optimizer.optimize_for_scenario(scenario)
        return {
            "success": True,
            "scenario": scenario,
            "settings": {
                "cache_enabled": performance_optimizer.enable_cache,
                "parallel_enabled": performance_optimizer.enable_parallel,
                "metrics_enabled": performance_optimizer.enable_metrics
            }
        }
    
    def get_cloud_platforms(self) -> List[Dict[str, Any]]:
        """Get available cloud platforms with credentials."""
        platforms = []
        for platform in cloud_manager.get_available_platforms():
            info = cloud_manager.get_platform_info(platform)
            info["available"] = True
            info["platform_id"] = platform.value
            platforms.append(info)
        return platforms
    
    def get_server_info(self) -> Dict[str, Any]:
        """
        Get MCP server information with enhanced capabilities.
        
        Returns:
            Server metadata with performance and cloud support info
        """
        tool_count = len(self.get_all_tools())
        cloud_platforms = self.get_cloud_platforms()
        perf_stats = performance_optimizer.get_performance_stats()
        
        return {
            "name": "webpilot-mcp",
            "version": "1.3.0",  # Updated version for extended tools + cloud + performance
            "description": f"WebPilot MCP server with {tool_count}+ web automation tools",
            "capabilities": {
                "tools": True,
                "resources": True,
                "prompts": False,
                "sampling": False,
                "cloud_testing": len(cloud_platforms) > 1,  # More than just local
                "performance_optimization": True,
                "error_recovery": True,
                "batch_execution": True
            },
            "tool_count": tool_count,
            "cloud_platforms": cloud_platforms,
            "performance": {
                "cache_enabled": performance_optimizer.enable_cache,
                "parallel_execution": performance_optimizer.enable_parallel,
                "cache_stats": perf_stats.get("cache_stats", {})
            },
            "enhancements": {
                "intelligent_error_handling": True,
                "performance_caching": True,
                "cloud_platform_support": True,
                "batch_operations": True,
                "60+_tools": True
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