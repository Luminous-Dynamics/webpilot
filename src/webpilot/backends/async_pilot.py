#!/usr/bin/env python3
"""
WebPilot Async - Asynchronous browser automation for better performance
"""

import asyncio
import aiohttp
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import subprocess

# Import base classes
from ..core import WebPilotSession, ActionResult, ActionType, BrowserType


class AsyncWebPilot:
    """Asynchronous WebPilot for improved performance"""
    
    def __init__(self, browser: BrowserType = BrowserType.FIREFOX,
                 headless: bool = False,
                 session: Optional[WebPilotSession] = None,
                 max_workers: int = 4):
        """Initialize async WebPilot"""
        
        self.browser = browser
        self.headless = headless
        self.session = session or WebPilotSession()
        self.logger = logging.getLogger(f'AsyncWebPilot.{self.session.session_id}')
        
        # Thread pool for blocking operations
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Async HTTP session
        self.http_session = None
        
        # Browser process
        self.browser_process = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.http_session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
        if self.http_session:
            await self.http_session.close()
    
    async def start(self, url: str) -> ActionResult:
        """Start browser asynchronously"""
        start_time = time.time()
        
        try:
            # Start browser in thread pool (blocking operation)
            loop = asyncio.get_event_loop()
            
            def start_browser():
                cmd = [self.browser.value]
                if self.headless:
                    cmd.append('--headless')
                cmd.append(url)
                
                return subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            
            self.browser_process = await loop.run_in_executor(
                self.executor,
                start_browser
            )
            
            # Wait a bit for browser to start
            await asyncio.sleep(3)
            
            # Update session
            self.session.state['browser_pid'] = self.browser_process.pid
            self.session.state['current_url'] = url
            self.session.save_state()
            
            duration = (time.time() - start_time) * 1000
            
            result = ActionResult(
                success=True,
                action_type=ActionType.NAVIGATE,
                data={
                    'url': url,
                    'pid': self.browser_process.pid,
                    'async': True
                },
                duration_ms=duration
            )
            
            self.logger.info(f"Async browser started: {url}")
            self.session.add_action(result)
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to start browser: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.NAVIGATE,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000
            )
    
    async def fetch_content(self, url: str) -> ActionResult:
        """Fetch page content asynchronously"""
        start_time = time.time()
        
        try:
            if not self.http_session:
                self.http_session = aiohttp.ClientSession()
            
            async with self.http_session.get(url) as response:
                content = await response.text()
                
                duration = (time.time() - start_time) * 1000
                
                result = ActionResult(
                    success=True,
                    action_type=ActionType.EXTRACT,
                    data={
                        'url': url,
                        'status': response.status,
                        'length': len(content),
                        'content_preview': content[:500],
                        'headers': dict(response.headers)
                    },
                    duration_ms=duration
                )
                
                self.logger.info(f"Fetched {len(content)} bytes from {url}")
                return result
                
        except Exception as e:
            self.logger.error(f"Fetch failed: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.EXTRACT,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000
            )
    
    async def batch_fetch(self, urls: List[str]) -> List[ActionResult]:
        """Fetch multiple URLs concurrently"""
        tasks = [self.fetch_content(url) for url in urls]
        results = await asyncio.gather(*tasks)
        return results
    
    async def screenshot_async(self, name: Optional[str] = None) -> ActionResult:
        """Take screenshot asynchronously"""
        start_time = time.time()
        
        try:
            filepath = self.session.get_screenshot_path(name)
            current_url = self.session.state.get('current_url', 'https://example.com')
            
            # Run screenshot command in executor
            loop = asyncio.get_event_loop()
            
            def take_screenshot():
                cmd = ['firefox', '--headless', '--screenshot', str(filepath), current_url]
                result = subprocess.run(cmd, capture_output=True, timeout=10)
                return result.returncode == 0 and filepath.exists()
            
            success = await loop.run_in_executor(
                self.executor,
                take_screenshot
            )
            
            if success:
                duration = (time.time() - start_time) * 1000
                
                self.session.state['screenshots'].append(str(filepath))
                self.session.save_state()
                
                result = ActionResult(
                    success=True,
                    action_type=ActionType.SCREENSHOT,
                    data={
                        'path': str(filepath),
                        'async': True
                    },
                    duration_ms=duration
                )
                
                self.logger.info(f"Async screenshot saved: {filepath}")
                self.session.add_action(result)
                return result
            else:
                raise Exception("Screenshot failed")
                
        except Exception as e:
            self.logger.error(f"Screenshot failed: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.SCREENSHOT,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000
            )
    
    async def parallel_actions(self, actions: List[Dict]) -> List[ActionResult]:
        """Execute multiple actions in parallel"""
        
        async def execute_action(action):
            action_type = action.get('type')
            
            if action_type == 'fetch':
                return await self.fetch_content(action['url'])
            elif action_type == 'screenshot':
                return await self.screenshot_async(action.get('name'))
            elif action_type == 'wait':
                await asyncio.sleep(action.get('seconds', 1))
                return ActionResult(
                    success=True,
                    action_type=ActionType.WAIT,
                    data={'seconds': action.get('seconds', 1)}
                )
            else:
                return ActionResult(
                    success=False,
                    action_type=ActionType.UNKNOWN,
                    error=f"Unknown action type: {action_type}"
                )
        
        tasks = [execute_action(action) for action in actions]
        results = await asyncio.gather(*tasks)
        return results
    
    async def wait(self, seconds: float) -> ActionResult:
        """Async wait"""
        start_time = time.time()
        
        await asyncio.sleep(seconds)
        
        duration = (time.time() - start_time) * 1000
        
        result = ActionResult(
            success=True,
            action_type=ActionType.WAIT,
            data={'seconds': seconds},
            duration_ms=duration
        )
        
        self.logger.info(f"Waited {seconds}s asynchronously")
        return result
    
    async def monitor_page(self, url: str, interval: int = 5, 
                          duration: int = 60) -> List[ActionResult]:
        """Monitor a page for changes over time"""
        
        results = []
        end_time = time.time() + duration
        
        while time.time() < end_time:
            # Fetch content
            result = await self.fetch_content(url)
            results.append(result)
            
            # Take screenshot
            screenshot = await self.screenshot_async(f"monitor_{int(time.time())}.png")
            results.append(screenshot)
            
            # Wait before next check
            await asyncio.sleep(interval)
        
        self.logger.info(f"Monitored {url} for {duration}s")
        return results
    
    async def close(self) -> ActionResult:
        """Close browser and cleanup"""
        start_time = time.time()
        
        try:
            if self.browser_process:
                self.browser_process.terminate()
                # Wait for process to end
                await asyncio.sleep(0.5)
                if self.browser_process.poll() is None:
                    self.browser_process.kill()
            
            # Cleanup executor
            self.executor.shutdown(wait=False)
            
            duration = (time.time() - start_time) * 1000
            
            result = ActionResult(
                success=True,
                action_type=ActionType.CLOSE,
                duration_ms=duration
            )
            
            self.logger.info("Async browser closed")
            return result
            
        except Exception as e:
            self.logger.error(f"Close failed: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.CLOSE,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000
            )


async def test_async_webpilot():
    """Test async WebPilot"""
    
    print("⚡ Testing Async WebPilot")
    print("=" * 50)
    
    async with AsyncWebPilot() as pilot:
        # Test browser start
        print("\n1. Starting browser asynchronously...")
        result = await pilot.start("https://example.com")
        print(f"   Start: {'✅' if result.success else '❌'}")
        if result.success:
            print(f"   PID: {result.data.get('pid')}")
            print(f"   Duration: {result.duration_ms:.1f}ms")
        
        # Test async content fetch
        print("\n2. Fetching content asynchronously...")
        result = await pilot.fetch_content("https://example.com")
        print(f"   Fetch: {'✅' if result.success else '❌'}")
        if result.success:
            print(f"   Content length: {result.data.get('length')} bytes")
            print(f"   Duration: {result.duration_ms:.1f}ms")
        
        # Test batch fetch
        print("\n3. Batch fetching multiple URLs...")
        urls = [
            "https://example.com",
            "https://github.com",
            "https://python.org"
        ]
        
        start = time.time()
        results = await pilot.batch_fetch(urls)
        batch_time = (time.time() - start) * 1000
        
        print(f"   Fetched {len(results)} URLs in {batch_time:.1f}ms")
        for i, result in enumerate(results):
            status = '✅' if result.success else '❌'
            print(f"   {urls[i]}: {status}")
        
        # Test parallel actions
        print("\n4. Executing parallel actions...")
        actions = [
            {'type': 'fetch', 'url': 'https://example.com'},
            {'type': 'screenshot', 'name': 'async_test.png'},
            {'type': 'wait', 'seconds': 1}
        ]
        
        start = time.time()
        results = await pilot.parallel_actions(actions)
        parallel_time = (time.time() - start) * 1000
        
        print(f"   Executed {len(results)} actions in {parallel_time:.1f}ms")
        for action, result in zip(actions, results):
            status = '✅' if result.success else '❌'
            print(f"   {action['type']}: {status}")
    
    print("\n✨ Async WebPilot test complete!")
    print("\nAsync capabilities:")
    print("  • Concurrent URL fetching")
    print("  • Parallel action execution")
    print("  • Non-blocking operations")
    print("  • Page monitoring")
    print("  • Improved performance")


def run_async_test():
    """Run async test"""
    asyncio.run(test_async_webpilot())


if __name__ == "__main__":
    run_async_test()