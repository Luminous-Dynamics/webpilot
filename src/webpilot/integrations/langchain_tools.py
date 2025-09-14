"""
LangChain Integration for WebPilot

Native LangChain tools for WebPilot, enabling use with 100+ LLMs
through LangChain's unified interface.
"""

from typing import Dict, Any, List, Optional, Type, Callable
from pydantic import BaseModel, Field
import json
import asyncio

try:
    from langchain.tools import BaseTool, StructuredTool
    from langchain.callbacks.manager import CallbackManagerForToolRun, AsyncCallbackManagerForToolRun
    from langchain.agents import Tool
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    # Create dummy classes for type hints
    class BaseTool:
        pass
    class StructuredTool:
        pass
    class Tool:
        pass
    class CallbackManagerForToolRun:
        pass
    class AsyncCallbackManagerForToolRun:
        pass

from ..core import WebPilot, ActionResult
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


# Input schemas for structured tools
class NavigateInput(BaseModel):
    """Input for navigation tool."""
    url: str = Field(..., description="URL to navigate to")


class ClickInput(BaseModel):
    """Input for click tool."""
    text: Optional[str] = Field(None, description="Text of element to click")
    selector: Optional[str] = Field(None, description="CSS selector of element")
    x: Optional[int] = Field(None, description="X coordinate")
    y: Optional[int] = Field(None, description="Y coordinate")


class TypeInput(BaseModel):
    """Input for typing tool."""
    text: str = Field(..., description="Text to type")
    selector: Optional[str] = Field(None, description="CSS selector of input field")
    clear_first: bool = Field(False, description="Clear field before typing")


class ScrollInput(BaseModel):
    """Input for scroll tool."""
    direction: str = Field("down", description="Direction: up, down, top, bottom")
    amount: int = Field(3, description="Amount to scroll")


class ScreenshotInput(BaseModel):
    """Input for screenshot tool."""
    filename: Optional[str] = Field(None, description="Filename for screenshot")
    full_page: bool = Field(False, description="Capture full page")


class ExtractInput(BaseModel):
    """Input for extraction tool."""
    selector: Optional[str] = Field(None, description="CSS selector to extract from")
    include_hidden: bool = Field(False, description="Include hidden elements")


class WebPilotTool(BaseTool):
    """
    Base WebPilot tool for LangChain.
    
    This provides a single tool that handles all WebPilot operations
    through natural language or structured commands.
    """
    
    name: str = "webpilot"
    description: str = """
    Professional web automation tool for browsing and interacting with websites.
    
    Capabilities:
    - Navigate to URLs
    - Click elements (by text, selector, or coordinates)
    - Type text into forms
    - Take screenshots
    - Extract page content
    - Scroll pages
    - Wait for elements
    - Handle multiple tabs
    - Fill forms automatically
    
    Examples:
    - "Navigate to https://google.com"
    - "Click the search button"
    - "Type 'Python tutorials' in the search box"
    - "Take a screenshot"
    - "Extract all links from the page"
    """
    
    pilot: Optional[WebPilot] = None
    session_active: bool = False
    
    def __init__(self, browser: str = "firefox", headless: bool = False):
        """Initialize WebPilot tool."""
        super().__init__()
        self.browser = browser
        self.headless = headless
        self.logger = get_logger(__name__)
        
    def _ensure_session(self) -> WebPilot:
        """Ensure WebPilot session is active."""
        if not self.pilot:
            self.pilot = WebPilot(browser=self.browser, headless=self.headless)
        if not self.session_active:
            self.pilot.start("about:blank")
            self.session_active = True
        return self.pilot
        
    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """
        Execute WebPilot command from natural language.
        
        Args:
            query: Natural language command or JSON structured command
            run_manager: LangChain callback manager
            
        Returns:
            Execution result as string
        """
        try:
            # Try to parse as JSON for structured commands
            try:
                command = json.loads(query)
                action = command.get("action")
                args = command.get("arguments", {})
            except (json.JSONDecodeError, TypeError):
                # Parse natural language
                action, args = self._parse_natural_language(query)
            
            # Execute action
            pilot = self._ensure_session()
            result = self._execute_action(pilot, action, args)
            
            # Format response
            if result.success:
                return f"✅ Success: {result.data}"
            else:
                return f"❌ Error: {result.error}"
                
        except Exception as e:
            self.logger.error(f"WebPilot tool error: {e}")
            return f"❌ Error: {str(e)}"
            
    async def _arun(
        self,
        query: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Async version of _run."""
        # For now, just run synchronously
        # TODO: Implement true async execution
        return self._run(query, run_manager)
        
    def _parse_natural_language(self, query: str) -> tuple[str, Dict[str, Any]]:
        """
        Parse natural language into action and arguments.
        
        Args:
            query: Natural language command
            
        Returns:
            Tuple of (action, arguments)
        """
        query_lower = query.lower()
        
        # Navigation
        if "navigate" in query_lower or "go to" in query_lower:
            import re
            url_match = re.search(r'https?://[^\s]+|www\.[^\s]+', query, re.IGNORECASE)
            if url_match:
                url = url_match.group()
                if not url.startswith("http"):
                    url = f"https://{url}"
                return "navigate", {"url": url}
        
        # Click
        if "click" in query_lower:
            # Extract what to click
            import re
            # Try to find quoted text
            quoted = re.findall(r'["\']([^"\']+)["\']', query)
            if quoted:
                return "click", {"text": quoted[0]}
            # Otherwise use words after "click"
            words = query.split()
            if "click" in words:
                idx = words.index("click")
                if idx < len(words) - 1:
                    target = " ".join(words[idx + 1:])
                    return "click", {"text": target}
        
        # Type/Enter text
        if "type" in query_lower or "enter" in query_lower or "write" in query_lower:
            import re
            quoted = re.findall(r'["\']([^"\']+)["\']', query)
            if quoted:
                return "type", {"text": quoted[0]}
        
        # Screenshot
        if "screenshot" in query_lower or "capture" in query_lower:
            return "screenshot", {}
        
        # Extract
        if "extract" in query_lower or "get" in query_lower:
            if "content" in query_lower or "text" in query_lower:
                return "extract", {}
            elif "links" in query_lower:
                return "extract_links", {}
        
        # Scroll
        if "scroll" in query_lower:
            if "up" in query_lower:
                return "scroll", {"direction": "up"}
            elif "down" in query_lower:
                return "scroll", {"direction": "down"}
            elif "top" in query_lower:
                return "scroll", {"direction": "top"}
            elif "bottom" in query_lower:
                return "scroll", {"direction": "bottom"}
            else:
                return "scroll", {"direction": "down"}
        
        # Default
        raise ValueError(f"Could not parse command: {query}")
        
    def _execute_action(self, pilot: WebPilot, action: str, args: Dict[str, Any]) -> ActionResult:
        """
        Execute WebPilot action.
        
        Args:
            pilot: WebPilot instance
            action: Action to execute
            args: Action arguments
            
        Returns:
            Action result
        """
        if action == "navigate":
            return pilot.navigate(args["url"])
        elif action == "click":
            return pilot.click(
                text=args.get("text"),
                selector=args.get("selector"),
                x=args.get("x"),
                y=args.get("y")
            )
        elif action == "type":
            return pilot.type_text(
                args["text"],
                selector=args.get("selector"),
                clear_first=args.get("clear_first", False)
            )
        elif action == "screenshot":
            return pilot.screenshot(
                args.get("filename"),
                full_page=args.get("full_page", False)
            )
        elif action == "extract":
            return pilot.extract_page_content()
        elif action == "scroll":
            return pilot.scroll(
                direction=args.get("direction", "down"),
                amount=args.get("amount", 3)
            )
        elif action == "wait":
            return pilot.wait(args.get("seconds", 1))
        elif action == "close":
            result = pilot.close()
            self.session_active = False
            return result
        else:
            raise ValueError(f"Unknown action: {action}")
    
    def close(self):
        """Close WebPilot session."""
        if self.pilot and self.session_active:
            self.pilot.close()
            self.session_active = False
            self.pilot = None


def create_webpilot_tools(browser: str = "firefox", headless: bool = False) -> List[StructuredTool]:
    """
    Create structured WebPilot tools for LangChain.
    
    This creates individual tools for each WebPilot action,
    providing more precise control than the single WebPilotTool.
    
    Args:
        browser: Browser to use
        headless: Run in headless mode
        
    Returns:
        List of structured tools
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("LangChain is not installed. Install with: pip install langchain")
    
    # Shared WebPilot instance
    pilot_container = {"pilot": None, "active": False}
    
    def ensure_pilot() -> WebPilot:
        """Ensure pilot is initialized."""
        if not pilot_container["pilot"]:
            pilot_container["pilot"] = WebPilot(browser=browser, headless=headless)
        return pilot_container["pilot"]
    
    # Tool implementations
    def navigate(url: str) -> str:
        """Navigate to a URL."""
        pilot = ensure_pilot()
        if not pilot_container["active"]:
            result = pilot.start(url)
            pilot_container["active"] = True
        else:
            result = pilot.navigate(url)
        return f"Navigated to {url}" if result.success else f"Failed: {result.error}"
    
    def click(text: str = None, selector: str = None, x: int = None, y: int = None) -> str:
        """Click on an element."""
        pilot = ensure_pilot()
        if not pilot_container["active"]:
            return "Error: No active session. Navigate to a URL first."
        result = pilot.click(text=text, selector=selector, x=x, y=y)
        return "Clicked element" if result.success else f"Failed: {result.error}"
    
    def type_text(text: str, selector: str = None, clear_first: bool = False) -> str:
        """Type text into an input field."""
        pilot = ensure_pilot()
        if not pilot_container["active"]:
            return "Error: No active session. Navigate to a URL first."
        result = pilot.type_text(text, selector=selector, clear_first=clear_first)
        return f"Typed: {text}" if result.success else f"Failed: {result.error}"
    
    def screenshot(filename: str = None, full_page: bool = False) -> str:
        """Take a screenshot."""
        pilot = ensure_pilot()
        if not pilot_container["active"]:
            return "Error: No active session. Navigate to a URL first."
        result = pilot.screenshot(filename, full_page=full_page)
        return f"Screenshot saved: {result.data}" if result.success else f"Failed: {result.error}"
    
    def extract_content(selector: str = None) -> str:
        """Extract page content."""
        pilot = ensure_pilot()
        if not pilot_container["active"]:
            return "Error: No active session. Navigate to a URL first."
        result = pilot.extract_page_content()
        if result.success:
            content = result.data
            if isinstance(content, dict):
                return json.dumps(content, indent=2)
            return str(content)
        return f"Failed: {result.error}"
    
    def scroll_page(direction: str = "down", amount: int = 3) -> str:
        """Scroll the page."""
        pilot = ensure_pilot()
        if not pilot_container["active"]:
            return "Error: No active session. Navigate to a URL first."
        result = pilot.scroll(direction=direction, amount=amount)
        return f"Scrolled {direction}" if result.success else f"Failed: {result.error}"
    
    def close_browser() -> str:
        """Close the browser session."""
        if pilot_container["pilot"] and pilot_container["active"]:
            result = pilot_container["pilot"].close()
            pilot_container["active"] = False
            pilot_container["pilot"] = None
            return "Browser closed"
        return "No active session"
    
    # Create structured tools
    tools = [
        StructuredTool.from_function(
            func=navigate,
            name="webpilot_navigate",
            description="Navigate to a URL and start browser session if needed",
            args_schema=NavigateInput
        ),
        StructuredTool.from_function(
            func=click,
            name="webpilot_click",
            description="Click on an element by text, selector, or coordinates",
            args_schema=ClickInput
        ),
        StructuredTool.from_function(
            func=type_text,
            name="webpilot_type",
            description="Type text into an input field",
            args_schema=TypeInput
        ),
        StructuredTool.from_function(
            func=screenshot,
            name="webpilot_screenshot",
            description="Take a screenshot of the current page",
            args_schema=ScreenshotInput
        ),
        StructuredTool.from_function(
            func=extract_content,
            name="webpilot_extract",
            description="Extract content from the current page",
            args_schema=ExtractInput
        ),
        StructuredTool.from_function(
            func=scroll_page,
            name="webpilot_scroll",
            description="Scroll the page in a direction",
            args_schema=ScrollInput
        ),
        StructuredTool.from_function(
            func=close_browser,
            name="webpilot_close",
            description="Close the browser session",
            return_direct=False
        )
    ]
    
    return tools


def create_webpilot_agent(llm, browser: str = "firefox", headless: bool = False, verbose: bool = True):
    """
    Create a LangChain agent with WebPilot tools.
    
    Args:
        llm: LangChain LLM instance
        browser: Browser to use
        headless: Run in headless mode
        verbose: Enable verbose output
        
    Returns:
        LangChain agent with WebPilot capabilities
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("LangChain is not installed. Install with: pip install langchain")
    
    from langchain.agents import initialize_agent, AgentType
    
    # Get WebPilot tools
    tools = create_webpilot_tools(browser=browser, headless=headless)
    
    # Create agent
    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=verbose,
        handle_parsing_errors=True,
        max_iterations=10
    )
    
    return agent


# Example usage functions
def example_with_ollama():
    """Example using WebPilot with Ollama local LLM."""
    if not LANGCHAIN_AVAILABLE:
        print("LangChain not available. Install with: pip install langchain langchain-community")
        return
        
    try:
        from langchain_community.llms import Ollama
    except ImportError:
        print("Ollama integration not available. Install with: pip install langchain-community")
        return
    
    # Initialize Ollama LLM
    llm = Ollama(model="llama2")
    
    # Create WebPilot agent
    agent = create_webpilot_agent(llm, headless=True)
    
    # Use the agent
    result = agent.run("Go to Python.org and find the download section")
    print(result)


def example_with_openai():
    """Example using WebPilot with OpenAI."""
    if not LANGCHAIN_AVAILABLE:
        print("LangChain not available. Install with: pip install langchain openai")
        return
    
    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        print("OpenAI integration not available. Install with: pip install langchain-openai")
        return
    
    # Initialize OpenAI LLM
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    
    # Create WebPilot agent
    agent = create_webpilot_agent(llm)
    
    # Use the agent
    result = agent.run("Navigate to GitHub and search for WebPilot repositories")
    print(result)


def example_simple_tool():
    """Example using WebPilot as a simple tool."""
    if not LANGCHAIN_AVAILABLE:
        print("LangChain not available")
        return
    
    # Create simple WebPilot tool
    tool = WebPilotTool()
    
    # Use directly
    result = tool._run("Navigate to https://example.com")
    print(result)
    
    result = tool._run("Take a screenshot")
    print(result)
    
    # Clean up
    tool.close()


if __name__ == "__main__":
    # Run examples
    print("WebPilot LangChain Integration Examples")
    print("=" * 50)
    
    print("\n1. Simple tool example:")
    example_simple_tool()
    
    print("\n2. Ollama example (requires Ollama running):")
    example_with_ollama()
    
    print("\n3. OpenAI example (requires API key):")
    example_with_openai()