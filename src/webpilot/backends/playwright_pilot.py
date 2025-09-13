#!/usr/bin/env python3
"""
WebPilot Playwright Backend - Modern browser automation
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

# Try importing Playwright
try:
    from playwright.async_api import async_playwright, Browser, Page, BrowserContext
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️  Playwright not available. Install with: pip install playwright && playwright install")

# Import base classes
from ..core import WebPilotSession, ActionResult, ActionType, BrowserType, WebPilotError

logger = logging.getLogger('WebPilot.Playwright')


class PlaywrightWebPilot:
    """WebPilot with Playwright backend for modern browser automation"""
    
    def __init__(self, browser_type: BrowserType = BrowserType.CHROMIUM, 
                 headless: bool = False,
                 session: Optional[WebPilotSession] = None):
        """Initialize Playwright-based WebPilot"""
        
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright not available. Install with:\n"
                "pip install playwright\n"
                "playwright install"
            )
        
        self.browser_type = browser_type
        self.headless = headless
        self.session = session or WebPilotSession()
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.logger = logging.getLogger(f'PlaywrightWebPilot.{self.session.session_id}')
    
    async def start(self, url: str) -> ActionResult:
        """Start browser and navigate to URL"""
        import time
        start_time = time.time()
        
        try:
            # Start Playwright
            self.playwright = await async_playwright().start()
            
            # Choose browser
            if self.browser_type == BrowserType.FIREFOX:
                browser_engine = self.playwright.firefox
            elif self.browser_type == BrowserType.CHROME:
                browser_engine = self.playwright.chromium
                # Use Chrome channel for actual Chrome
                launch_options = {'channel': 'chrome', 'headless': self.headless}
            elif self.browser_type == BrowserType.CHROMIUM:
                browser_engine = self.playwright.chromium
                launch_options = {'headless': self.headless}
            else:
                browser_engine = self.playwright.chromium
                launch_options = {'headless': self.headless}
            
            # Launch browser
            self.browser = await browser_engine.launch(
                headless=self.headless,
                args=['--window-size=1920,1080']
            )
            
            # Create context with viewport
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='WebPilot/1.0 (Playwright)'
            )
            
            # Create page
            self.page = await self.context.new_page()
            
            # Navigate to URL
            response = await self.page.goto(url, wait_until='networkidle')
            
            # Update session
            self.session.state['current_url'] = url
            self.session.state['browser_type'] = 'playwright'
            self.session.save_state()
            
            duration = (time.time() - start_time) * 1000
            
            result = ActionResult(
                success=True,
                action_type=ActionType.NAVIGATE,
                data={
                    'url': url,
                    'title': await self.page.title(),
                    'status': response.status if response else None,
                    'backend': 'playwright'
                },
                duration_ms=duration
            )
            
            self.logger.info(f"Playwright browser started: {url}")
            self.session.add_action(result)
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to start Playwright browser: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.NAVIGATE,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000
            )
    
    async def navigate(self, url: str) -> ActionResult:
        """Navigate to URL"""
        import time
        start_time = time.time()
        
        try:
            if not self.page:
                return await self.start(url)
            
            response = await self.page.goto(url, wait_until='networkidle')
            self.session.state['current_url'] = url
            self.session.save_state()
            
            duration = (time.time() - start_time) * 1000
            
            result = ActionResult(
                success=True,
                action_type=ActionType.NAVIGATE,
                data={
                    'url': url,
                    'title': await self.page.title(),
                    'status': response.status if response else None
                },
                duration_ms=duration
            )
            
            self.session.add_action(result)
            return result
            
        except Exception as e:
            self.logger.error(f"Navigation failed: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.NAVIGATE,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000
            )
    
    async def screenshot(self, filename: str = None) -> ActionResult:
        """Take a screenshot"""
        import time
        start_time = time.time()
        
        try:
            if not self.page:
                raise WebPilotError("Browser not started")
            
            if not filename:
                filename = f"screenshot_{int(time.time())}.png"
            
            screenshot_path = self.session.screenshot_dir / filename
            await self.page.screenshot(path=str(screenshot_path), full_page=True)
            
            duration = (time.time() - start_time) * 1000
            
            result = ActionResult(
                success=True,
                action_type=ActionType.SCREENSHOT,
                data={
                    'path': str(screenshot_path),
                    'filename': filename
                },
                duration_ms=duration
            )
            
            self.session.add_action(result)
            return result
            
        except Exception as e:
            self.logger.error(f"Screenshot failed: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.SCREENSHOT,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000
            )
    
    async def click(self, selector: str) -> ActionResult:
        """Click an element"""
        import time
        start_time = time.time()
        
        try:
            if not self.page:
                raise WebPilotError("Browser not started")
            
            await self.page.click(selector)
            
            duration = (time.time() - start_time) * 1000
            
            result = ActionResult(
                success=True,
                action_type=ActionType.CLICK,
                data={'selector': selector},
                duration_ms=duration
            )
            
            self.session.add_action(result)
            return result
            
        except Exception as e:
            self.logger.error(f"Click failed: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.CLICK,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000
            )
    
    async def type_text(self, selector: str, text: str) -> ActionResult:
        """Type text into an element"""
        import time
        start_time = time.time()
        
        try:
            if not self.page:
                raise WebPilotError("Browser not started")
            
            await self.page.type(selector, text)
            
            duration = (time.time() - start_time) * 1000
            
            result = ActionResult(
                success=True,
                action_type=ActionType.TYPE,
                data={'selector': selector, 'text': text},
                duration_ms=duration
            )
            
            self.session.add_action(result)
            return result
            
        except Exception as e:
            self.logger.error(f"Type failed: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.TYPE,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000
            )
    
    async def wait_for_selector(self, selector: str, timeout: int = 30000) -> ActionResult:
        """Wait for an element to appear"""
        import time
        start_time = time.time()
        
        try:
            if not self.page:
                raise WebPilotError("Browser not started")
            
            await self.page.wait_for_selector(selector, timeout=timeout)
            
            duration = (time.time() - start_time) * 1000
            
            result = ActionResult(
                success=True,
                action_type=ActionType.WAIT,
                data={'selector': selector},
                duration_ms=duration
            )
            
            self.session.add_action(result)
            return result
            
        except Exception as e:
            self.logger.error(f"Wait failed: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.WAIT,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000
            )
    
    async def evaluate(self, script: str) -> ActionResult:
        """Execute JavaScript in the page"""
        import time
        start_time = time.time()
        
        try:
            if not self.page:
                raise WebPilotError("Browser not started")
            
            result_value = await self.page.evaluate(script)
            
            duration = (time.time() - start_time) * 1000
            
            result = ActionResult(
                success=True,
                action_type=ActionType.EXECUTE_JS,
                data={'result': result_value},
                duration_ms=duration
            )
            
            self.session.add_action(result)
            return result
            
        except Exception as e:
            self.logger.error(f"JavaScript execution failed: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.EXECUTE_JS,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000
            )
    
    async def close(self) -> ActionResult:
        """Close the browser"""
        import time
        start_time = time.time()
        
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            
            duration = (time.time() - start_time) * 1000
            
            result = ActionResult(
                success=True,
                action_type=ActionType.CLOSE,
                data={},
                duration_ms=duration
            )
            
            self.logger.info("Playwright browser closed")
            self.session.add_action(result)
            return result
            
        except Exception as e:
            self.logger.error(f"Close failed: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.CLOSE,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000
            )
    
    # Context manager support
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


class SyncPlaywrightWebPilot:
    """Synchronous wrapper for Playwright backend"""
    
    def __init__(self, *args, **kwargs):
        self.async_pilot = PlaywrightWebPilot(*args, **kwargs)
        self.loop = asyncio.new_event_loop()
    
    def start(self, url: str) -> ActionResult:
        return self.loop.run_until_complete(self.async_pilot.start(url))
    
    def navigate(self, url: str) -> ActionResult:
        return self.loop.run_until_complete(self.async_pilot.navigate(url))
    
    def screenshot(self, filename: str = None) -> ActionResult:
        return self.loop.run_until_complete(self.async_pilot.screenshot(filename))
    
    def click(self, selector: str) -> ActionResult:
        return self.loop.run_until_complete(self.async_pilot.click(selector))
    
    def type_text(self, selector: str, text: str) -> ActionResult:
        return self.loop.run_until_complete(self.async_pilot.type_text(selector, text))
    
    def close(self) -> ActionResult:
        return self.loop.run_until_complete(self.async_pilot.close())
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        self.loop.close()