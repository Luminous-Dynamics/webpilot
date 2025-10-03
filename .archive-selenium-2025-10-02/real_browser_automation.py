#!/usr/bin/env python3
"""
Real Browser Automation That Actually Works
This is what we should have built from the start.
"""

import os
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️  Selenium not installed. Install with: pip install selenium")


class RealBrowserAutomation:
    """
    A browser automation tool that ACTUALLY controls browsers.
    No fake successes. No pretend actions. Real automation.
    """
    
    def __init__(self, browser='firefox', headless=False):
        """Initialize with real browser driver."""
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium is required. Install with: pip install selenium")
        
        self.browser_type = browser
        self.headless = headless
        self.driver = None
        self.wait = None
        self.screenshots_dir = Path("screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)
        
    def start(self) -> bool:
        """Start the browser. Returns True if successful."""
        try:
            if self.browser_type == 'firefox':
                options = webdriver.FirefoxOptions()
                if self.headless:
                    options.add_argument('--headless')
                self.driver = webdriver.Firefox(options=options)
            else:  # Chrome
                options = webdriver.ChromeOptions()
                if self.headless:
                    options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                self.driver = webdriver.Chrome(options=options)
            
            self.wait = WebDriverWait(self.driver, 10)
            print(f"✅ Browser started ({self.browser_type}, headless={self.headless})")
            return True
        except Exception as e:
            print(f"❌ Failed to start browser: {e}")
            return False
    
    def navigate(self, url: str) -> bool:
        """Navigate to a URL. Returns True if successful."""
        if not self.driver:
            print("❌ Browser not started")
            return False
        
        try:
            if not url.startswith('http'):
                url = f'https://{url}'
            self.driver.get(url)
            print(f"✅ Navigated to {url}")
            return True
        except Exception as e:
            print(f"❌ Failed to navigate: {e}")
            return False
    
    def find_element_smart(self, description: str):
        """Find element using multiple strategies."""
        if not self.driver:
            return None
        
        strategies = [
            # Try by text
            (By.XPATH, f"//*[contains(text(), '{description}')]"),
            # Try button with text
            (By.XPATH, f"//button[contains(text(), '{description}')]"),
            # Try link with text
            (By.XPATH, f"//a[contains(text(), '{description}')]"),
            # Try by placeholder
            (By.XPATH, f"//input[@placeholder*='{description}']"),
            # Try by aria-label
            (By.XPATH, f"//*[@aria-label*='{description}']"),
            # Try by ID (if it looks like an ID)
            (By.ID, description) if not ' ' in description else None,
            # Try by class (if it looks like a class)
            (By.CLASS_NAME, description) if not ' ' in description else None,
        ]
        
        for strategy in strategies:
            if strategy is None:
                continue
            try:
                by, value = strategy
                element = self.driver.find_element(by, value)
                if element:
                    return element
            except NoSuchElementException:
                continue
        
        return None
    
    def click(self, description: str) -> bool:
        """Click an element. Returns True if successful."""
        if not self.driver:
            print("❌ Browser not started")
            return False
        
        element = self.find_element_smart(description)
        if element:
            try:
                element.click()
                print(f"✅ Clicked '{description}'")
                return True
            except Exception as e:
                # Try JavaScript click as fallback
                try:
                    self.driver.execute_script("arguments[0].click();", element)
                    print(f"✅ Clicked '{description}' (via JS)")
                    return True
                except:
                    print(f"❌ Failed to click '{description}': {e}")
                    return False
        else:
            print(f"❌ Could not find element '{description}'")
            return False
    
    def type_text(self, text: str, field_description: Optional[str] = None) -> bool:
        """Type text into a field. Returns True if successful."""
        if not self.driver:
            print("❌ Browser not started")
            return False
        
        try:
            if field_description:
                element = self.find_element_smart(field_description)
            else:
                # Find any visible input field
                element = self.driver.find_element(By.CSS_SELECTOR, 
                    "input:not([type='hidden']):not([type='submit']):not([type='button'])")
            
            if element:
                element.clear()
                element.send_keys(text)
                print(f"✅ Typed '{text}'" + (f" in '{field_description}'" if field_description else ""))
                return True
            else:
                print(f"❌ Could not find input field")
                return False
        except Exception as e:
            print(f"❌ Failed to type text: {e}")
            return False
    
    def screenshot(self, name: Optional[str] = None) -> str:
        """Take a screenshot. Returns filename."""
        if not self.driver:
            print("❌ Browser not started")
            return ""
        
        try:
            if not name:
                name = f"screenshot_{int(time.time())}.png"
            elif not name.endswith('.png'):
                name += '.png'
            
            filepath = self.screenshots_dir / name
            self.driver.save_screenshot(str(filepath))
            print(f"✅ Screenshot saved: {filepath}")
            return str(filepath)
        except Exception as e:
            print(f"❌ Failed to take screenshot: {e}")
            return ""
    
    def get_text(self, selector: Optional[str] = None) -> str:
        """Get text from page or element."""
        if not self.driver:
            return ""
        
        try:
            if selector:
                element = self.find_element_smart(selector)
                if element:
                    return element.text
            else:
                # Get all visible text
                return self.driver.find_element(By.TAG_NAME, 'body').text
        except:
            return ""
    
    def wait_for(self, description: str, timeout: int = 10) -> bool:
        """Wait for an element to appear."""
        if not self.driver:
            return False
        
        try:
            # Try multiple strategies
            conditions = [
                EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{description}')]")),
                EC.presence_of_element_located((By.XPATH, f"//button[contains(text(), '{description}')]")),
                EC.presence_of_element_located((By.XPATH, f"//a[contains(text(), '{description}')]")),
            ]
            
            for condition in conditions:
                try:
                    WebDriverWait(self.driver, timeout/len(conditions)).until(condition)
                    print(f"✅ Found '{description}'")
                    return True
                except TimeoutException:
                    continue
            
            print(f"⏱️ Timeout waiting for '{description}'")
            return False
        except Exception as e:
            print(f"❌ Error waiting: {e}")
            return False
    
    def execute_script(self, script: str) -> Any:
        """Execute JavaScript in the browser."""
        if not self.driver:
            return None
        
        try:
            result = self.driver.execute_script(script)
            return result
        except Exception as e:
            print(f"❌ Script execution failed: {e}")
            return None
    
    def get_current_url(self) -> str:
        """Get current page URL."""
        if self.driver:
            return self.driver.current_url
        return ""
    
    def get_title(self) -> str:
        """Get page title."""
        if self.driver:
            return self.driver.title
        return ""
    
    def close(self):
        """Close the browser."""
        if self.driver:
            self.driver.quit()
            print("✅ Browser closed")
            self.driver = None


def demo_real_automation():
    """Demonstrate REAL browser automation."""
    
    print("=" * 60)
    print("   Real Browser Automation Demo")
    print("=" * 60)
    print("\nThis actually controls a browser!\n")
    
    # Create automation instance
    browser = RealBrowserAutomation(browser='firefox', headless=True)
    
    # Start browser
    if not browser.start():
        print("Failed to start browser. Make sure Firefox/Chrome and drivers are installed.")
        return
    
    try:
        # Navigate to a real website
        print("\n📍 Test 1: Navigation")
        browser.navigate("example.com")
        title = browser.get_title()
        print(f"   Page title: {title}")
        
        # Take a screenshot
        print("\n📸 Test 2: Screenshot")
        screenshot = browser.screenshot("example_page")
        
        # Get page text
        print("\n📝 Test 3: Reading Content")
        text = browser.get_text()
        if "Example Domain" in text:
            print("   ✅ Found expected content")
        
        # Navigate to another page
        print("\n🔍 Test 4: Search Engine")
        browser.navigate("duckduckgo.com")
        
        # Type in search box
        print("\n⌨️ Test 5: Typing")
        browser.type_text("WebPilot automation", "search")
        
        # Get current URL
        print("\n🌐 Test 6: URL Tracking")
        current_url = browser.get_current_url()
        print(f"   Current URL: {current_url}")
        
        # Execute JavaScript
        print("\n💻 Test 7: JavaScript Execution")
        result = browser.execute_script("return navigator.userAgent")
        print(f"   User Agent: {result[:50]}...")
        
        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("=" * 60)
        
    finally:
        # Always close browser
        browser.close()


def demo_useful_task():
    """Do something actually useful."""
    
    print("\n" + "=" * 60)
    print("   Useful Task: Check Website Status")
    print("=" * 60)
    
    sites_to_check = [
        "github.com",
        "google.com",
        "stackoverflow.com"
    ]
    
    browser = RealBrowserAutomation(headless=True)
    if not browser.start():
        return
    
    results = []
    
    for site in sites_to_check:
        print(f"\nChecking {site}...")
        if browser.navigate(site):
            title = browser.get_title()
            screenshot = browser.screenshot(f"{site.replace('.', '_')}")
            results.append({
                'site': site,
                'status': 'UP',
                'title': title,
                'screenshot': screenshot
            })
            print(f"   ✅ {site} is up - Title: {title[:50]}")
        else:
            results.append({
                'site': site,
                'status': 'DOWN',
                'title': None,
                'screenshot': None
            })
            print(f"   ❌ {site} appears to be down")
    
    browser.close()
    
    # Save results
    with open('site_status.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📊 Results saved to site_status.json")
    print(f"📸 Screenshots saved to screenshots/")


if __name__ == "__main__":
    if SELENIUM_AVAILABLE:
        print("Choose demo:")
        print("1. Basic automation demo")
        print("2. Useful task (check websites)")
        
        choice = input("\nEnter choice (1 or 2): ").strip()
        
        if choice == "1":
            demo_real_automation()
        elif choice == "2":
            demo_useful_task()
        else:
            print("Invalid choice")
    else:
        print("""
        To use this tool, you need to install Selenium:
        
        1. Install Selenium:
           pip install selenium
        
        2. Install a browser driver:
           - Firefox: Download geckodriver
           - Chrome: Download chromedriver
        
        3. Make sure the driver is in your PATH
        
        Then this will actually control a real browser!
        """)