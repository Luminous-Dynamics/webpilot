"""
OpenAI Adapter for WebPilot

Enables WebPilot to work with OpenAI's function calling API,
making it compatible with ChatGPT, GPT-4, and Azure OpenAI.
"""

import json
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
import asyncio
from enum import Enum

from ..core import WebPilot, ActionResult
from ..mcp.server import WebPilotMCPServer
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class ToolCategory(Enum):
    """Categories of WebPilot tools for organization."""
    NAVIGATION = "navigation"
    INTERACTION = "interaction"
    EXTRACTION = "extraction"
    TESTING = "testing"
    AUTOMATION = "automation"
    CLOUD = "cloud"
    UTILITY = "utility"


@dataclass
class OpenAIFunction:
    """OpenAI function definition format."""
    name: str
    description: str
    parameters: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to OpenAI function format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


class OpenAIAdapter:
    """
    Adapter to make WebPilot compatible with OpenAI's function calling API.
    
    This enables WebPilot to work with:
    - ChatGPT (via API)
    - GPT-4 and GPT-3.5
    - Azure OpenAI Service
    - Any OpenAI-compatible API
    """
    
    def __init__(self, browser: str = "firefox", headless: bool = False):
        """
        Initialize the OpenAI adapter.
        
        Args:
            browser: Browser to use (firefox, chrome, chromium)
            headless: Run browser in headless mode
        """
        self.pilot: Optional[WebPilot] = None
        self.mcp_server = WebPilotMCPServer()
        self.browser = browser
        self.headless = headless
        self.logger = get_logger(__name__)
        self.session_active = False
        
    def get_functions(self, categories: Optional[List[ToolCategory]] = None) -> List[Dict[str, Any]]:
        """
        Get all WebPilot functions in OpenAI format.
        
        Args:
            categories: Optional list of categories to include
            
        Returns:
            List of OpenAI-formatted function definitions
        """
        functions = []
        
        # Core navigation functions
        if not categories or ToolCategory.NAVIGATION in categories:
            functions.extend([
                OpenAIFunction(
                    name="navigate_to_url",
                    description="Start a browser session and navigate to a URL",
                    parameters={
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "The URL to navigate to"
                            },
                            "wait_for_load": {
                                "type": "boolean",
                                "description": "Wait for page to fully load",
                                "default": True
                            }
                        },
                        "required": ["url"]
                    }
                ),
                OpenAIFunction(
                    name="go_back",
                    description="Navigate back in browser history",
                    parameters={
                        "type": "object",
                        "properties": {}
                    }
                ),
                OpenAIFunction(
                    name="refresh_page",
                    description="Refresh the current page",
                    parameters={
                        "type": "object",
                        "properties": {}
                    }
                ),
            ])
        
        # Interaction functions
        if not categories or ToolCategory.INTERACTION in categories:
            functions.extend([
                OpenAIFunction(
                    name="click_element",
                    description="Click on an element on the page",
                    parameters={
                        "type": "object",
                        "properties": {
                            "selector": {
                                "type": "string",
                                "description": "CSS selector of the element to click"
                            },
                            "text": {
                                "type": "string",
                                "description": "Text content of the element to click (alternative to selector)"
                            },
                            "wait_after": {
                                "type": "number",
                                "description": "Seconds to wait after clicking",
                                "default": 0
                            }
                        }
                    }
                ),
                OpenAIFunction(
                    name="type_text",
                    description="Type text into an input field",
                    parameters={
                        "type": "object",
                        "properties": {
                            "selector": {
                                "type": "string",
                                "description": "CSS selector of the input field"
                            },
                            "text": {
                                "type": "string",
                                "description": "Text to type"
                            },
                            "clear_first": {
                                "type": "boolean",
                                "description": "Clear the field before typing",
                                "default": False
                            },
                            "press_enter": {
                                "type": "boolean",
                                "description": "Press Enter after typing",
                                "default": False
                            }
                        },
                        "required": ["text"]
                    }
                ),
                OpenAIFunction(
                    name="select_option",
                    description="Select an option from a dropdown",
                    parameters={
                        "type": "object",
                        "properties": {
                            "selector": {
                                "type": "string",
                                "description": "CSS selector of the select element"
                            },
                            "value": {
                                "type": "string",
                                "description": "Value or text of the option to select"
                            }
                        },
                        "required": ["selector", "value"]
                    }
                ),
                OpenAIFunction(
                    name="scroll_page",
                    description="Scroll the page",
                    parameters={
                        "type": "object",
                        "properties": {
                            "direction": {
                                "type": "string",
                                "enum": ["up", "down", "top", "bottom"],
                                "description": "Direction to scroll"
                            },
                            "amount": {
                                "type": "integer",
                                "description": "Amount to scroll (for up/down)",
                                "default": 3
                            }
                        },
                        "required": ["direction"]
                    }
                ),
            ])
        
        # Data extraction functions
        if not categories or ToolCategory.EXTRACTION in categories:
            functions.extend([
                OpenAIFunction(
                    name="get_page_content",
                    description="Extract all text content from the current page",
                    parameters={
                        "type": "object",
                        "properties": {
                            "include_hidden": {
                                "type": "boolean",
                                "description": "Include hidden elements",
                                "default": False
                            }
                        }
                    }
                ),
                OpenAIFunction(
                    name="get_element_text",
                    description="Get text from a specific element",
                    parameters={
                        "type": "object",
                        "properties": {
                            "selector": {
                                "type": "string",
                                "description": "CSS selector of the element"
                            }
                        },
                        "required": ["selector"]
                    }
                ),
                OpenAIFunction(
                    name="extract_links",
                    description="Extract all links from the page",
                    parameters={
                        "type": "object",
                        "properties": {
                            "pattern": {
                                "type": "string",
                                "description": "Optional regex pattern to filter links"
                            }
                        }
                    }
                ),
                OpenAIFunction(
                    name="extract_images",
                    description="Extract all image URLs from the page",
                    parameters={
                        "type": "object",
                        "properties": {
                            "min_size": {
                                "type": "integer",
                                "description": "Minimum image size in pixels",
                                "default": 0
                            }
                        }
                    }
                ),
                OpenAIFunction(
                    name="extract_table_data",
                    description="Extract data from tables on the page",
                    parameters={
                        "type": "object",
                        "properties": {
                            "table_selector": {
                                "type": "string",
                                "description": "CSS selector for specific table (optional)"
                            }
                        }
                    }
                ),
            ])
        
        # Testing functions
        if not categories or ToolCategory.TESTING in categories:
            functions.extend([
                OpenAIFunction(
                    name="take_screenshot",
                    description="Take a screenshot of the current page",
                    parameters={
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "Filename for the screenshot"
                            },
                            "full_page": {
                                "type": "boolean",
                                "description": "Capture full page or just viewport",
                                "default": False
                            }
                        }
                    }
                ),
                OpenAIFunction(
                    name="check_element_exists",
                    description="Check if an element exists on the page",
                    parameters={
                        "type": "object",
                        "properties": {
                            "selector": {
                                "type": "string",
                                "description": "CSS selector of the element"
                            }
                        },
                        "required": ["selector"]
                    }
                ),
                OpenAIFunction(
                    name="wait_for_element",
                    description="Wait for an element to appear",
                    parameters={
                        "type": "object",
                        "properties": {
                            "selector": {
                                "type": "string",
                                "description": "CSS selector of the element"
                            },
                            "timeout": {
                                "type": "integer",
                                "description": "Maximum seconds to wait",
                                "default": 10
                            }
                        },
                        "required": ["selector"]
                    }
                ),
                OpenAIFunction(
                    name="get_page_metrics",
                    description="Get page performance metrics",
                    parameters={
                        "type": "object",
                        "properties": {}
                    }
                ),
            ])
        
        # Automation functions
        if not categories or ToolCategory.AUTOMATION in categories:
            functions.extend([
                OpenAIFunction(
                    name="fill_form",
                    description="Automatically fill a form with data",
                    parameters={
                        "type": "object",
                        "properties": {
                            "form_data": {
                                "type": "object",
                                "description": "Key-value pairs of field names/selectors and values"
                            },
                            "submit": {
                                "type": "boolean",
                                "description": "Submit the form after filling",
                                "default": False
                            }
                        },
                        "required": ["form_data"]
                    }
                ),
                OpenAIFunction(
                    name="login",
                    description="Perform login action",
                    parameters={
                        "type": "object",
                        "properties": {
                            "username": {
                                "type": "string",
                                "description": "Username or email"
                            },
                            "password": {
                                "type": "string",
                                "description": "Password"
                            },
                            "username_selector": {
                                "type": "string",
                                "description": "CSS selector for username field"
                            },
                            "password_selector": {
                                "type": "string",
                                "description": "CSS selector for password field"
                            },
                            "submit_selector": {
                                "type": "string",
                                "description": "CSS selector for submit button"
                            }
                        },
                        "required": ["username", "password"]
                    }
                ),
                OpenAIFunction(
                    name="download_file",
                    description="Download a file from a link",
                    parameters={
                        "type": "object",
                        "properties": {
                            "link_selector": {
                                "type": "string",
                                "description": "CSS selector of the download link"
                            },
                            "wait_for_download": {
                                "type": "boolean",
                                "description": "Wait for download to complete",
                                "default": True
                            }
                        },
                        "required": ["link_selector"]
                    }
                ),
            ])
        
        # Utility functions
        if not categories or ToolCategory.UTILITY in categories:
            functions.extend([
                OpenAIFunction(
                    name="execute_javascript",
                    description="Execute JavaScript code on the page",
                    parameters={
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "JavaScript code to execute"
                            }
                        },
                        "required": ["code"]
                    }
                ),
                OpenAIFunction(
                    name="get_cookies",
                    description="Get cookies from the current domain",
                    parameters={
                        "type": "object",
                        "properties": {}
                    }
                ),
                OpenAIFunction(
                    name="set_cookie",
                    description="Set a cookie",
                    parameters={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Cookie name"
                            },
                            "value": {
                                "type": "string",
                                "description": "Cookie value"
                            },
                            "domain": {
                                "type": "string",
                                "description": "Cookie domain"
                            }
                        },
                        "required": ["name", "value"]
                    }
                ),
                OpenAIFunction(
                    name="close_browser",
                    description="Close the browser session",
                    parameters={
                        "type": "object",
                        "properties": {}
                    }
                ),
            ])
        
        return [f.to_dict() for f in functions]
    
    async def execute_function(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a WebPilot function from OpenAI function call.
        
        Args:
            function_name: Name of the function to execute
            arguments: Function arguments
            
        Returns:
            Execution result in OpenAI-compatible format
        """
        try:
            # Map OpenAI function names to WebPilot actions
            result = await self._execute_webpilot_action(function_name, arguments)
            
            # Format response for OpenAI
            if result.get("success"):
                return {
                    "status": "success",
                    "result": result.get("data"),
                    "message": f"Successfully executed {function_name}"
                }
            else:
                return {
                    "status": "error",
                    "error": result.get("error"),
                    "message": f"Failed to execute {function_name}"
                }
                
        except Exception as e:
            self.logger.error(f"Error executing function {function_name}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": f"Exception during {function_name}"
            }
    
    async def _execute_webpilot_action(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Internal method to execute WebPilot actions.
        
        Args:
            function_name: OpenAI function name
            arguments: Function arguments
            
        Returns:
            WebPilot execution result
        """
        # Initialize pilot if needed
        if function_name == "navigate_to_url" or (not self.session_active and function_name != "close_browser"):
            if not self.pilot:
                self.pilot = WebPilot(browser=self.browser, headless=self.headless)
            if not self.session_active:
                result = self.pilot.start(arguments.get("url", "about:blank"))
                self.session_active = True
                if function_name == "navigate_to_url":
                    return {"success": result.success, "data": result.data, "error": result.error}
        
        # Map functions to WebPilot methods
        if function_name == "navigate_to_url":
            result = self.pilot.navigate(arguments["url"])
        elif function_name == "click_element":
            result = self.pilot.click(
                selector=arguments.get("selector"),
                text=arguments.get("text")
            )
        elif function_name == "type_text":
            result = self.pilot.type_text(
                arguments["text"],
                selector=arguments.get("selector"),
                clear_first=arguments.get("clear_first", False)
            )
        elif function_name == "scroll_page":
            result = self.pilot.scroll(
                direction=arguments["direction"],
                amount=arguments.get("amount", 3)
            )
        elif function_name == "take_screenshot":
            result = self.pilot.screenshot(
                filename=arguments.get("filename"),
                full_page=arguments.get("full_page", False)
            )
        elif function_name == "get_page_content":
            result = self.pilot.extract_page_content()
        elif function_name == "close_browser":
            if self.pilot:
                result = self.pilot.close()
                self.pilot = None
                self.session_active = False
            else:
                result = ActionResult(success=True, data="No active session")
        else:
            # For unmapped functions, try to use MCP server
            mcp_result = await self.mcp_server.handle_tool_call(
                f"webpilot_{function_name}",
                arguments
            )
            return mcp_result
        
        return {
            "success": result.success,
            "data": result.data,
            "error": result.error
        }
    
    def get_function_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific function definition by name.
        
        Args:
            name: Function name
            
        Returns:
            Function definition or None
        """
        all_functions = self.get_functions()
        for func in all_functions:
            if func["function"]["name"] == name:
                return func
        return None
    
    def get_simplified_functions(self) -> List[Dict[str, Any]]:
        """
        Get a simplified set of the most commonly used functions.
        
        Returns:
            List of core WebPilot functions for basic automation
        """
        return self.get_functions(categories=[
            ToolCategory.NAVIGATION,
            ToolCategory.INTERACTION,
            ToolCategory.EXTRACTION
        ])
    
    def create_openai_client_example(self) -> str:
        """
        Generate example code for using WebPilot with OpenAI client.
        
        Returns:
            Python code example
        """
        return '''
from openai import OpenAI
from webpilot.adapters import OpenAIAdapter

# Initialize
client = OpenAI()
webpilot = OpenAIAdapter()

# Get available functions
functions = webpilot.get_functions()

# Create a message with function calling
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "Go to example.com and take a screenshot"}
    ],
    functions=functions,
    function_call="auto"
)

# Execute the function call
if response.choices[0].message.function_call:
    function_name = response.choices[0].message.function_call.name
    arguments = json.loads(response.choices[0].message.function_call.arguments)
    
    result = await webpilot.execute_function(function_name, arguments)
    print(f"Result: {result}")
'''