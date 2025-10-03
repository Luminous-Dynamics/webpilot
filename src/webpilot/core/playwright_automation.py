#!/usr/bin/env python3
"""
Modern Browser Automation Using Playwright
Replaces real_browser_automation.py with superior performance and reliability.

Key Improvements over Selenium:
- Auto-waiting (no manual WebDriverWait)
- Text selectors ("text=Sign in")
- Network interception
- Multi-browser support
- Built-in trace viewer
- 2-3x faster execution
"""

from pathlib import Path
from typing import Optional, Dict, Any, List, Union, Callable
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext, Playwright
import json
import time


class PlaywrightAutomation:
    """
    Modern browser automation using Playwright.
    Drop-in replacement for RealBrowserAutomation with enhanced capabilities.
    """

    def __init__(
        self,
        browser_type: str = 'firefox',
        headless: bool = False,
        slow_mo: int = 0,
        timeout: int = 30000
    ):
        """
        Initialize Playwright automation.

        Args:
            browser_type: 'firefox', 'chromium', or 'webkit'
            headless: Run without GUI
            slow_mo: Slow down operations by N milliseconds (useful for debugging)
            timeout: Default timeout for operations in milliseconds
        """
        self.browser_type = browser_type
        self.headless = headless
        self.slow_mo = slow_mo
        self.default_timeout = timeout

        # Playwright instances
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        # State tracking
        self.screenshots_dir = Path("screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)
        self.session_log: List[Dict[str, Any]] = []
        self.network_logs: List[Dict[str, Any]] = []

    def start(self) -> bool:
        """
        Start browser with automatic driver management.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Start Playwright (auto-handles driver installation!)
            self.playwright = sync_playwright().start()

            # Get browser launcher
            browser_launcher = getattr(self.playwright, self.browser_type)

            # Launch browser
            self.browser = browser_launcher.launch(
                headless=self.headless,
                slow_mo=self.slow_mo
            )

            # Create context (like a session with cookies, storage, etc.)
            self.context = self.browser.new_context(
                viewport={'width': 1366, 'height': 768},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) WebPilot/2.0'
            )

            # Set default timeout
            self.context.set_default_timeout(self.default_timeout)

            # Create page
            self.page = self.context.new_page()

            # Log action
            self._log_action('start', {'browser': self.browser_type, 'headless': self.headless})

            print(f"✅ Browser started ({self.browser_type}, headless={self.headless})")
            return True

        except Exception as e:
            print(f"❌ Failed to start browser: {e}")
            print("💡 Try running: playwright install")
            return False

    def navigate(self, url: str, wait_until: str = 'domcontentloaded') -> bool:
        """
        Navigate to URL with auto-waiting.

        Args:
            url: URL to navigate to
            wait_until: When to consider navigation successful
                       ('load', 'domcontentloaded', 'networkidle')

        Returns:
            True if successful, False otherwise
        """
        if not self.page:
            print("❌ Browser not started")
            return False

        try:
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                url = f'https://{url}'

            # Navigate (auto-waits for page load!)
            self.page.goto(url, wait_until=wait_until)

            # Log action
            self._log_action('navigate', {'url': url})

            print(f"✅ Navigated to {url}")
            return True

        except Exception as e:
            print(f"❌ Failed to navigate to {url}: {e}")
            return False

    def click(self, selector: str, timeout: Optional[int] = None) -> bool:
        """
        Click element with auto-waiting.

        Supports multiple selector types:
        - Text: "text=Sign in" or just "Sign in"
        - CSS: "button.login"
        - XPath: "xpath=//button[@id='login']"
        - Role: "role=button[name='Submit']"

        Args:
            selector: Element selector
            timeout: Override default timeout

        Returns:
            True if successful, False otherwise
        """
        if not self.page:
            return False

        try:
            # Auto-add text= if it looks like plain text
            if not any(selector.startswith(prefix) for prefix in ['text=', 'css=', 'xpath=', 'role=', '//', '.', '#']):
                selector = f'text={selector}'

            # Click (auto-waits for element to be clickable!)
            self.page.click(selector, timeout=timeout or self.default_timeout)

            # Log action
            self._log_action('click', {'selector': selector})

            print(f"✅ Clicked: {selector}")
            return True

        except Exception as e:
            print(f"❌ Failed to click '{selector}': {e}")
            return False

    def type_text(self, selector: str, text: str, timeout: Optional[int] = None, delay: int = 0) -> bool:
        """
        Type text into field with auto-waiting.

        Args:
            selector: Element selector
            text: Text to type
            timeout: Override default timeout
            delay: Delay between keystrokes in milliseconds (simulates human typing)

        Returns:
            True if successful, False otherwise
        """
        if not self.page:
            return False

        try:
            # Fill field (auto-waits for element!)
            if delay > 0:
                # Type with delay (human-like)
                self.page.type(selector, text, delay=delay, timeout=timeout or self.default_timeout)
            else:
                # Fill instantly
                self.page.fill(selector, text, timeout=timeout or self.default_timeout)

            # Log action (don't log sensitive data in production!)
            self._log_action('type', {'selector': selector, 'length': len(text)})

            print(f"✅ Typed text into: {selector}")
            return True

        except Exception as e:
            print(f"❌ Failed to type into '{selector}': {e}")
            return False

    def screenshot(self, name: str = "screenshot", full_page: bool = False) -> Optional[Path]:
        """
        Take screenshot with auto-path handling.

        Args:
            name: Screenshot name (without extension)
            full_page: Capture entire scrollable page

        Returns:
            Path to screenshot or None if failed
        """
        if not self.page:
            return None

        try:
            path = self.screenshots_dir / f"{name}.png"

            # Take screenshot
            self.page.screenshot(path=str(path), full_page=full_page)

            # Log action
            self._log_action('screenshot', {'path': str(path), 'full_page': full_page})

            print(f"📸 Screenshot saved: {path}")
            return path

        except Exception as e:
            print(f"❌ Failed to take screenshot: {e}")
            return None

    def get_text(self, selector: Optional[str] = None) -> str:
        """
        Get text from element or entire page.

        Args:
            selector: Element selector (None for entire page)

        Returns:
            Text content or empty string if failed
        """
        if not self.page:
            return ""

        try:
            if selector:
                # Get text from specific element
                element = self.page.query_selector(selector)
                return element.text_content() if element else ""
            else:
                # Get all visible text
                return self.page.inner_text('body')

        except Exception as e:
            print(f"❌ Failed to get text: {e}")
            return ""

    def get_title(self) -> str:
        """Get page title."""
        if not self.page:
            return ""

        try:
            return self.page.title()
        except Exception:
            return ""

    def get_url(self) -> str:
        """Get current URL."""
        if not self.page:
            return ""

        try:
            return self.page.url
        except Exception:
            return ""

    def wait_for(self, selector: str, state: str = 'visible', timeout: Optional[int] = None) -> bool:
        """
        Wait for element state.

        Args:
            selector: Element selector
            state: Element state ('attached', 'detached', 'visible', 'hidden')
            timeout: Override default timeout

        Returns:
            True if element reached state, False otherwise
        """
        if not self.page:
            return False

        try:
            self.page.wait_for_selector(
                selector,
                state=state,
                timeout=timeout or self.default_timeout
            )
            return True
        except Exception:
            return False

    def execute_script(self, script: str) -> Any:
        """
        Execute JavaScript on page.

        Args:
            script: JavaScript code to execute

        Returns:
            Result of script execution or None if failed
        """
        if not self.page:
            return None

        try:
            result = self.page.evaluate(script)
            self._log_action('script', {'script': script[:100]})
            return result
        except Exception as e:
            print(f"❌ Failed to execute script: {e}")
            return None

    def go_back(self) -> bool:
        """Navigate back in history."""
        if not self.page:
            return False

        try:
            self.page.go_back()
            self._log_action('back', {})
            return True
        except Exception:
            return False

    def go_forward(self) -> bool:
        """Navigate forward in history."""
        if not self.page:
            return False

        try:
            self.page.go_forward()
            self._log_action('forward', {})
            return True
        except Exception:
            return False

    def reload(self) -> bool:
        """Reload current page."""
        if not self.page:
            return False

        try:
            self.page.reload()
            self._log_action('reload', {})
            return True
        except Exception:
            return False

    def get_elements(self, selector: str) -> List[Any]:
        """
        Get all elements matching selector.

        Args:
            selector: Element selector

        Returns:
            List of elements
        """
        if not self.page:
            return []

        try:
            return self.page.query_selector_all(selector)
        except Exception:
            return []

    def enable_network_logging(self):
        """Enable network request/response logging (Playwright advantage!)"""
        if not self.page:
            return

        def log_request(request):
            self.network_logs.append({
                'type': 'request',
                'method': request.method,
                'url': request.url,
                'resource_type': request.resource_type,
                'timestamp': time.time()
            })

        def log_response(response):
            self.network_logs.append({
                'type': 'response',
                'status': response.status,
                'url': response.url,
                'timestamp': time.time()
            })

        self.page.on("request", log_request)
        self.page.on("response", log_response)

        print("📡 Network logging enabled")

    def get_network_logs(self) -> List[Dict[str, Any]]:
        """Get recorded network logs."""
        return self.network_logs

    def block_resources(self, resource_types: List[str]):
        """
        Block resource types to speed up tests (Playwright advantage!)

        Args:
            resource_types: Types to block (e.g., ['image', 'stylesheet', 'font'])
        """
        if not self.page:
            return

        def block_route(route):
            if route.request.resource_type in resource_types:
                route.abort()
            else:
                route.continue_()

        self.page.route("**/*", block_route)
        print(f"🚫 Blocking resources: {', '.join(resource_types)}")

    def save_session_log(self, filename: str = "session_log.json"):
        """Save session log to file."""
        try:
            with open(filename, 'w') as f:
                json.dump(self.session_log, f, indent=2)
            print(f"📝 Session log saved: {filename}")
        except Exception as e:
            print(f"❌ Failed to save session log: {e}")

    def close(self):
        """Clean up all resources."""
        try:
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()

            self._log_action('close', {})
            print("✅ Browser closed")

        except Exception as e:
            print(f"⚠️  Error during cleanup: {e}")

    def _log_action(self, action: str, details: Dict[str, Any]):
        """Internal: Log action to session log."""
        self.session_log.append({
            'timestamp': time.time(),
            'action': action,
            'details': details
        })

    def __enter__(self):
        """Context manager support."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Automatic cleanup."""
        self.close()
        return False


# Convenience functions

def quick_screenshot(url: str, output: str = "screenshot.png", headless: bool = True) -> bool:
    """
    Quick screenshot of a URL.

    Example:
        quick_screenshot("github.com", "github.png")
    """
    with PlaywrightAutomation(headless=headless) as browser:
        if browser.navigate(url):
            return browser.screenshot(output.replace('.png', '')) is not None
    return False


def quick_page_text(url: str, headless: bool = True) -> str:
    """
    Quick extraction of page text.

    Example:
        text = quick_page_text("github.com")
    """
    with PlaywrightAutomation(headless=headless) as browser:
        if browser.navigate(url):
            return browser.get_text()
    return ""


# Example usage
if __name__ == "__main__":
    print("🚀 Playwright Automation Demo\n")

    # Example 1: Context manager (recommended)
    with PlaywrightAutomation(browser_type='firefox', headless=False) as browser:
        # Navigate
        browser.navigate("github.com")

        # Take screenshot
        browser.screenshot("github_home")

        # Get title
        title = browser.get_title()
        print(f"Page title: {title}")

        # Click using text (Playwright magic!)
        browser.click("Sign in")

        # Enable network logging
        browser.enable_network_logging()

        # Navigate somewhere
        browser.go_back()

        # Get network stats
        logs = browser.get_network_logs()
        print(f"Network requests: {len([l for l in logs if l['type'] == 'request'])}")

        # Save session log
        browser.save_session_log()

    print("\n✨ Demo complete! Check screenshots/ and session_log.json")
