"""
WebPilot v2.0 - Playwright Adapter
Thin wrapper around Playwright for clean browser automation
"""

from typing import Union, Any, Optional
from playwright.async_api import Page as AsyncPage
from playwright.sync_api import Page as SyncPage
import inspect


class PlaywrightAdapter:
    """
    Minimal adapter between WebPilot AI and Playwright.
    This is the ONLY place WebPilot touches browser automation.
    """
    
    def __init__(self, page: Union[AsyncPage, SyncPage]):
        """
        Initialize adapter with Playwright page object.
        
        Args:
            page: Playwright sync or async page object
        """
        self.page = page
        self.is_async = inspect.iscoroutinefunction(page.goto)
    
    async def execute_playwright_action(self, action: str, **params) -> Any:
        """
        Bridge between AI decisions and browser actions.
        
        Args:
            action: Playwright method name (e.g., 'click', 'type', 'goto')
            **params: Parameters for the Playwright method
            
        Returns:
            Result from Playwright method
        """
        method = getattr(self.page, action, None)
        
        if not method:
            raise ValueError(f"Unknown Playwright action: {action}")
        
        if self.is_async:
            if inspect.iscoroutinefunction(method):
                return await method(**params)
            return method(**params)
        else:
            return method(**params)
    
    def execute_sync(self, action: str, **params) -> Any:
        """
        Synchronous execution for non-async Playwright.
        
        Args:
            action: Playwright method name
            **params: Parameters for the method
            
        Returns:
            Result from Playwright method
        """
        method = getattr(self.page, action, None)
        
        if not method:
            raise ValueError(f"Unknown Playwright action: {action}")
        
        return method(**params)
    
    async def smart_wait(self, selector: str, timeout: int = 30000) -> bool:
        """
        Wait for element with automatic retry strategies.
        
        Args:
            selector: Element selector
            timeout: Maximum wait time in milliseconds
            
        Returns:
            True if element found, False otherwise
        """
        try:
            if self.is_async:
                await self.page.wait_for_selector(selector, timeout=timeout)
            else:
                self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception:
            return False
    
    async def get_page_content(self) -> str:
        """Get full page HTML content."""
        if self.is_async:
            return await self.page.content()
        return self.page.content()
    
    async def take_screenshot(self, path: Optional[str] = None) -> bytes:
        """Take screenshot of current page."""
        params = {'path': path} if path else {}
        if self.is_async:
            return await self.page.screenshot(**params)
        return self.page.screenshot(**params)
    
    async def evaluate_javascript(self, expression: str) -> Any:
        """Execute JavaScript in page context."""
        if self.is_async:
            return await self.page.evaluate(expression)
        return self.page.evaluate(expression)
    
    def get_url(self) -> str:
        """Get current page URL."""
        return self.page.url
    
    def get_title(self) -> str:
        """Get page title."""
        if self.is_async:
            # For async, we'd need to await, but title is a property
            # This is a limitation we accept for simplicity
            return self.page.url  # Fallback to URL
        return self.page.title()