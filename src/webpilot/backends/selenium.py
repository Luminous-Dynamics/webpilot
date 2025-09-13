#!/usr/bin/env python3
"""
WebPilot Selenium Backend - Enhanced browser control
"""

import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import json
import base64
from dataclasses import dataclass
from enum import Enum

# Try importing Selenium
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️  Selenium not available. Install with: nix-shell -p python3Packages.selenium geckodriver")

# Import base classes
from ..core import WebPilotSession, ActionResult, ActionType, BrowserType


class SeleniumWebPilot:
    """WebPilot with Selenium backend for enhanced control"""
    
    def __init__(self, browser: BrowserType = BrowserType.FIREFOX, 
                 headless: bool = False,
                 session: Optional[WebPilotSession] = None):
        """Initialize Selenium-based WebPilot"""
        
        if not SELENIUM_AVAILABLE:
            raise ImportError(
                "Selenium not available. Install with:\n"
                "nix-shell -p python3Packages.selenium geckodriver\n"
                "or: pip install selenium webdriver-manager"
            )
        
        self.browser_type = browser
        self.headless = headless
        self.session = session or WebPilotSession()
        self.driver = None
        self.wait = None
        self.logger = logging.getLogger(f'SeleniumWebPilot.{self.session.session_id}')
        
    def start(self, url: str) -> ActionResult:
        """Start browser and navigate to URL"""
        start_time = time.time()
        
        try:
            # Setup browser options
            if self.browser_type == BrowserType.FIREFOX:
                options = FirefoxOptions()
                if self.headless:
                    options.add_argument('--headless')
                options.add_argument('--width=1920')
                options.add_argument('--height=1080')
                
                # Try to use system geckodriver
                try:
                    self.driver = webdriver.Firefox(options=options)
                except:
                    # Fallback to webdriver-manager
                    from webdriver_manager.firefox import GeckoDriverManager
                    self.driver = webdriver.Firefox(
                        executable_path=GeckoDriverManager().install(),
                        options=options
                    )
                    
            elif self.browser_type in [BrowserType.CHROME, BrowserType.CHROMIUM]:
                options = ChromeOptions()
                if self.headless:
                    options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--window-size=1920,1080')
                
                try:
                    self.driver = webdriver.Chrome(options=options)
                except:
                    from webdriver_manager.chrome import ChromeDriverManager
                    self.driver = webdriver.Chrome(
                        executable_path=ChromeDriverManager().install(),
                        options=options
                    )
            
            # Create wait object
            self.wait = WebDriverWait(self.driver, 10)
            
            # Navigate to URL
            self.driver.get(url)
            
            # Update session
            self.session.state['browser_pid'] = self.driver.service.process.pid if hasattr(self.driver, 'service') else None
            self.session.state['current_url'] = url
            self.session.save_state()
            
            duration = (time.time() - start_time) * 1000
            
            result = ActionResult(
                success=True,
                action_type=ActionType.NAVIGATE,
                data={
                    'url': url,
                    'title': self.driver.title,
                    'backend': 'selenium'
                },
                duration_ms=duration
            )
            
            self.logger.info(f"Selenium browser started: {url}")
            self.session.add_action(result)
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to start Selenium browser: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.NAVIGATE,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000
            )
    
    def navigate(self, url: str) -> ActionResult:
        """Navigate to URL"""
        start_time = time.time()
        
        try:
            if not self.driver:
                return self.start(url)
            
            self.driver.get(url)
            self.session.state['current_url'] = url
            self.session.save_state()
            
            duration = (time.time() - start_time) * 1000
            
            result = ActionResult(
                success=True,
                action_type=ActionType.NAVIGATE,
                data={'url': url, 'title': self.driver.title},
                duration_ms=duration
            )
            
            self.logger.info(f"Navigated to: {url}")
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
    
    def screenshot(self, name: Optional[str] = None) -> ActionResult:
        """Take screenshot using Selenium"""
        start_time = time.time()
        
        try:
            if not self.driver:
                raise Exception("Browser not started. Use start() first.")
            
            filepath = self.session.get_screenshot_path(name)
            
            # Selenium native screenshot
            self.driver.save_screenshot(str(filepath))
            
            # Also get base64 for Claude integration
            screenshot_base64 = self.driver.get_screenshot_as_base64()
            
            duration = (time.time() - start_time) * 1000
            
            self.session.state['screenshots'].append(str(filepath))
            self.session.save_state()
            
            result = ActionResult(
                success=True,
                action_type=ActionType.SCREENSHOT,
                data={
                    'path': str(filepath),
                    'size': filepath.stat().st_size,
                    'base64_preview': screenshot_base64[:100] + '...',
                    'method': 'selenium'
                },
                duration_ms=duration
            )
            
            self.logger.info(f"Screenshot saved: {filepath}")
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
    
    def click(self, x: Optional[int] = None, y: Optional[int] = None,
              selector: Optional[str] = None, text: Optional[str] = None) -> ActionResult:
        """Click element using various methods"""
        start_time = time.time()
        
        try:
            if not self.driver:
                raise Exception("Browser not started. Use start() first.")
            
            element = None
            
            # Method 1: Click by selector
            if selector:
                element = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            
            # Method 2: Click by text
            elif text:
                element = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, f"//*[contains(text(), '{text}')]"))
                )
            
            # Method 3: Click by coordinates
            elif x is not None and y is not None:
                actions = ActionChains(self.driver)
                actions.move_by_offset(x, y).click().perform()
                
                duration = (time.time() - start_time) * 1000
                result = ActionResult(
                    success=True,
                    action_type=ActionType.CLICK,
                    data={'x': x, 'y': y, 'method': 'coordinates'},
                    duration_ms=duration
                )
                self.session.add_action(result)
                return result
            
            if element:
                element.click()
                
                duration = (time.time() - start_time) * 1000
                result = ActionResult(
                    success=True,
                    action_type=ActionType.CLICK,
                    data={'selector': selector, 'text': text, 'method': 'element'},
                    duration_ms=duration
                )
                
                self.logger.info(f"Clicked element: {selector or text}")
                self.session.add_action(result)
                return result
            else:
                raise Exception("No element found to click")
                
        except Exception as e:
            self.logger.error(f"Click failed: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.CLICK,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000
            )
    
    def type_text(self, text: str, selector: Optional[str] = None,
                  clear_first: bool = False) -> ActionResult:
        """Type text into element"""
        start_time = time.time()
        
        try:
            if not self.driver:
                raise Exception("Browser not started. Use start() first.")
            
            if selector:
                element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                if clear_first:
                    element.clear()
                element.send_keys(text)
            else:
                # Type into active element
                active = self.driver.switch_to.active_element
                if clear_first:
                    active.clear()
                active.send_keys(text)
            
            duration = (time.time() - start_time) * 1000
            
            result = ActionResult(
                success=True,
                action_type=ActionType.TYPE,
                data={'text': text[:50], 'selector': selector},
                duration_ms=duration
            )
            
            self.logger.info(f"Typed text: {text[:50]}...")
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
    
    def wait_for_element(self, selector: str, timeout: int = 10) -> ActionResult:
        """Wait for element to appear"""
        start_time = time.time()
        
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            
            duration = (time.time() - start_time) * 1000
            
            result = ActionResult(
                success=True,
                action_type=ActionType.WAIT,
                data={'selector': selector, 'found': True},
                duration_ms=duration
            )
            
            self.logger.info(f"Element found: {selector}")
            return result
            
        except Exception as e:
            self.logger.error(f"Wait failed: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.WAIT,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000
            )
    
    def execute_javascript(self, script: str) -> ActionResult:
        """Execute JavaScript in browser"""
        start_time = time.time()
        
        try:
            if not self.driver:
                raise Exception("Browser not started. Use start() first.")
            
            result_value = self.driver.execute_script(script)
            
            duration = (time.time() - start_time) * 1000
            
            result = ActionResult(
                success=True,
                action_type=ActionType.SCRIPT,
                data={'script': script[:100], 'result': str(result_value)},
                duration_ms=duration
            )
            
            self.logger.info(f"Executed JavaScript")
            return result
            
        except Exception as e:
            self.logger.error(f"JavaScript execution failed: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.SCRIPT,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000
            )
    
    def get_page_source(self) -> ActionResult:
        """Get page HTML source"""
        start_time = time.time()
        
        try:
            if not self.driver:
                raise Exception("Browser not started. Use start() first.")
            
            source = self.driver.page_source
            
            duration = (time.time() - start_time) * 1000
            
            result = ActionResult(
                success=True,
                action_type=ActionType.EXTRACT,
                data={
                    'length': len(source),
                    'preview': source[:500],
                    'title': self.driver.title
                },
                duration_ms=duration
            )
            
            self.logger.info(f"Extracted {len(source)} bytes of HTML")
            return result
            
        except Exception as e:
            self.logger.error(f"Page source extraction failed: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.EXTRACT,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000
            )
    
    def find_elements(self, selector: str) -> List[Dict]:
        """Find all elements matching selector"""
        try:
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            return [
                {
                    'text': elem.text,
                    'tag': elem.tag_name,
                    'location': elem.location,
                    'size': elem.size,
                    'displayed': elem.is_displayed()
                }
                for elem in elements
            ]
        except Exception as e:
            self.logger.error(f"Find elements failed: {e}")
            return []
    
    def close(self) -> ActionResult:
        """Close browser"""
        start_time = time.time()
        
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
            
            duration = (time.time() - start_time) * 1000
            
            result = ActionResult(
                success=True,
                action_type=ActionType.CLOSE,
                duration_ms=duration
            )
            
            self.logger.info("Browser closed")
            return result
            
        except Exception as e:
            self.logger.error(f"Close failed: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.CLOSE,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000
            )
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure browser is closed"""
        self.close()


def test_selenium_backend():
    """Test Selenium backend"""
    
    if not SELENIUM_AVAILABLE:
        print("❌ Selenium not available. Install with:")
        print("   nix-shell -p python3Packages.selenium geckodriver")
        print("   or: pip install selenium webdriver-manager")
        return
    
    print("🚁 Testing Selenium WebPilot Backend")
    print("=" * 50)
    
    with SeleniumWebPilot(headless=True) as pilot:
        # Test navigation
        print("\n1. Testing navigation...")
        result = pilot.start("https://example.com")
        print(f"   Navigate: {'✅' if result.success else '❌'}")
        if result.success:
            print(f"   Title: {result.data.get('title')}")
        
        # Test screenshot
        print("\n2. Testing screenshot...")
        result = pilot.screenshot("selenium_test.png")
        print(f"   Screenshot: {'✅' if result.success else '❌'}")
        
        # Test JavaScript execution
        print("\n3. Testing JavaScript...")
        result = pilot.execute_javascript("return document.title")
        print(f"   JavaScript: {'✅' if result.success else '❌'}")
        if result.success:
            print(f"   Result: {result.data.get('result')}")
        
        # Test element finding
        print("\n4. Testing element finding...")
        elements = pilot.find_elements("h1")
        print(f"   Found {len(elements)} h1 elements")
        
        print("\n✨ Selenium backend test complete!")


if __name__ == "__main__":
    test_selenium_backend()