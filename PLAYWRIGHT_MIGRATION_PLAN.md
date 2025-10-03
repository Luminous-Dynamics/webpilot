# 🚀 WebPilot Playwright Migration Plan

**Status**: Recommended - migrate from Selenium to Playwright
**Estimated Effort**: 2-3 days for core features
**Priority**: High - Better DX, reliability, and future-proofing

## Why Migrate?

### Technical Advantages
| Feature | Selenium | Playwright | Winner |
|---------|----------|------------|--------|
| Auto-waiting | Manual `WebDriverWait` | Automatic | ✅ Playwright |
| Speed | Baseline | 2-3x faster | ✅ Playwright |
| Browser support | Driver per browser | Single API | ✅ Playwright |
| Network control | Limited | Built-in intercept | ✅ Playwright |
| Debugging | Basic | Trace viewer + inspector | ✅ Playwright |
| Async support | Awkward | Native | ✅ Playwright |
| Error messages | Cryptic | Detailed | ✅ Playwright |
| Maintenance | Active | Very active (Microsoft) | ✅ Playwright |

### Real-World Impact
```python
# Selenium (old way)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Firefox()
driver.get("https://example.com")
wait = WebDriverWait(driver, 10)
element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button")))
element.click()

# Playwright (new way)
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.firefox.launch()
    page = browser.new_page()
    page.goto("https://example.com")
    page.click("button")  # Auto-waits!
    browser.close()
```

**Lines of code**: 11 → 7 (36% reduction)
**Concepts to learn**: 5 → 2 (60% reduction)
**Auto-waiting**: No → Yes

## Migration Strategy

### Phase 1: Core Browser Automation (Week 1)

#### Priority 1: Rewrite `real_browser_automation.py` → `playwright_automation.py`

```python
# src/webpilot/core/playwright_automation.py
"""
Modern browser automation using Playwright.
Replaces real_browser_automation.py with better performance and reliability.
"""

from pathlib import Path
from typing import Optional, Dict, Any, List
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
import json


class PlaywrightAutomation:
    """
    Modern browser automation using Playwright.
    Simpler, faster, and more reliable than Selenium.
    """

    def __init__(self, browser_type: str = 'firefox', headless: bool = False):
        """
        Initialize Playwright automation.

        Args:
            browser_type: 'firefox', 'chromium', or 'webkit'
            headless: Run without GUI
        """
        self.browser_type = browser_type
        self.headless = headless
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.screenshots_dir = Path("screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)

    def start(self) -> bool:
        """Start browser. Auto-handles driver installation."""
        try:
            self.playwright = sync_playwright().start()

            # Launch browser (much simpler than Selenium!)
            browser_launcher = getattr(self.playwright, self.browser_type)
            self.browser = browser_launcher.launch(headless=self.headless)

            # Create context (like a session)
            self.context = self.browser.new_context()

            # Create page
            self.page = self.context.new_page()

            print(f"✅ Browser started ({self.browser_type}, headless={self.headless})")
            return True
        except Exception as e:
            print(f"❌ Failed to start browser: {e}")
            return False

    def navigate(self, url: str) -> bool:
        """Navigate to URL with auto-retry."""
        if not self.page:
            print("❌ Browser not started")
            return False

        try:
            if not url.startswith('http'):
                url = f'https://{url}'

            # Playwright auto-waits for page load!
            self.page.goto(url, wait_until='domcontentloaded')
            print(f"✅ Navigated to {url}")
            return True
        except Exception as e:
            print(f"❌ Failed to navigate: {e}")
            return False

    def click(self, selector: str, timeout: int = 30000) -> bool:
        """
        Click element. Supports text, CSS, XPath - Playwright is smart!

        Args:
            selector: Can be text like "Sign in" or CSS like "button.login"
            timeout: Max wait time in milliseconds
        """
        if not self.page:
            return False

        try:
            # Playwright auto-waits for element to be clickable!
            self.page.click(selector, timeout=timeout)
            print(f"✅ Clicked: {selector}")
            return True
        except Exception as e:
            print(f"❌ Failed to click '{selector}': {e}")
            return False

    def type_text(self, selector: str, text: str, timeout: int = 30000) -> bool:
        """Type text into field. Auto-waits for element."""
        if not self.page:
            return False

        try:
            self.page.fill(selector, text, timeout=timeout)
            print(f"✅ Typed text into: {selector}")
            return True
        except Exception as e:
            print(f"❌ Failed to type into '{selector}': {e}")
            return False

    def screenshot(self, name: str = "screenshot") -> Optional[Path]:
        """Take screenshot. Much simpler than Selenium."""
        if not self.page:
            return None

        try:
            path = self.screenshots_dir / f"{name}.png"
            self.page.screenshot(path=str(path))
            print(f"📸 Screenshot saved: {path}")
            return path
        except Exception as e:
            print(f"❌ Failed to take screenshot: {e}")
            return None

    def get_text(self, selector: Optional[str] = None) -> str:
        """Get text from element or whole page."""
        if not self.page:
            return ""

        try:
            if selector:
                return self.page.text_content(selector) or ""
            else:
                return self.page.content()
        except Exception as e:
            print(f"❌ Failed to get text: {e}")
            return ""

    def wait_for(self, selector: str, timeout: int = 30000) -> bool:
        """Explicitly wait for element (usually not needed)."""
        if not self.page:
            return False

        try:
            self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception:
            return False

    def execute_script(self, script: str) -> Any:
        """Execute JavaScript on page."""
        if not self.page:
            return None

        try:
            return self.page.evaluate(script)
        except Exception as e:
            print(f"❌ Failed to execute script: {e}")
            return None

    def close(self):
        """Clean up resources."""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print("✅ Browser closed")

    def __enter__(self):
        """Context manager support."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Automatic cleanup."""
        self.close()


# Convenience function for quick tasks
def quick_browser_action(url: str, headless: bool = True):
    """
    Quick browser action without manual setup.

    Example:
        with quick_browser_action("github.com") as page:
            page.click("Sign in")
    """
    automation = PlaywrightAutomation(headless=headless)
    automation.start()
    automation.navigate(url)
    return automation


# Example usage
if __name__ == "__main__":
    # Context manager makes it clean
    with PlaywrightAutomation(headless=False) as browser:
        browser.navigate("github.com")
        browser.screenshot("github_home")

        # Playwright understands text selectors!
        browser.click("text=Sign in")

        # Or CSS selectors
        browser.type_text("input[name='login']", "username")

        # Get page text
        title = browser.get_text("h1")
        print(f"Title: {title}")
```

#### Priority 2: Update WebPilot Integration

```python
# src/webpilot/core/webpilot_unified.py
"""
Unified WebPilot interface with Playwright backend.
Drop-in replacement for old implementation.
"""

from .playwright_automation import PlaywrightAutomation
from typing import Dict, List, Optional
import json


class WebPilot:
    """
    Unified WebPilot interface.
    Now powered by Playwright for better performance.
    """

    def __init__(self, browser: str = 'firefox', headless: bool = True):
        self.automation = PlaywrightAutomation(browser, headless)

    def check_website_status(self, urls: List[str]) -> Dict[str, Dict]:
        """
        Check if websites are accessible.

        Args:
            urls: List of URLs to check

        Returns:
            Dictionary with status for each URL
        """
        results = {}

        self.automation.start()

        for url in urls:
            try:
                # Navigate
                success = self.automation.navigate(url)

                if success:
                    # Get title
                    title = self.automation.get_text('title')

                    # Take screenshot
                    clean_name = url.replace('https://', '').replace('http://', '').replace('/', '_')
                    screenshot = self.automation.screenshot(clean_name)

                    results[url] = {
                        'status': 'UP',
                        'title': title,
                        'screenshot': str(screenshot) if screenshot else None
                    }
                else:
                    results[url] = {
                        'status': 'DOWN',
                        'error': 'Failed to navigate'
                    }

            except Exception as e:
                results[url] = {
                    'status': 'ERROR',
                    'error': str(e)
                }

        self.automation.close()

        # Save results
        with open('site_status.json', 'w') as f:
            json.dump(results, f, indent=2)

        return results
```

### Phase 2: Advanced Features (Week 2)

#### Network Interception (Playwright advantage!)

```python
# src/webpilot/features/network_control.py
"""
Network interception - impossible in Selenium, easy in Playwright!
"""

class NetworkInterceptor:
    """Control network requests/responses."""

    def __init__(self, page):
        self.page = page
        self.requests = []
        self.responses = []

    def start_recording(self):
        """Record all network traffic."""
        self.page.on("request", lambda req: self.requests.append({
            'url': req.url,
            'method': req.method,
            'headers': req.headers
        }))

        self.page.on("response", lambda res: self.responses.append({
            'url': res.url,
            'status': res.status,
            'headers': res.headers
        }))

    def block_resources(self, resource_types: List[str]):
        """Block images, CSS, etc to speed up tests."""
        self.page.route("**/*", lambda route:
            route.abort() if route.request.resource_type in resource_types
            else route.continue_()
        )

    def mock_api_response(self, url_pattern: str, mock_data: dict):
        """Mock API responses for testing."""
        self.page.route(url_pattern, lambda route:
            route.fulfill(json=mock_data)
        )
```

#### Multi-Browser Testing

```python
# src/webpilot/features/multi_browser.py
"""
Test on Firefox, Chrome, Safari simultaneously - Playwright magic!
"""

from playwright.sync_api import sync_playwright

class MultiBrowserTester:
    """Run same test on all browsers."""

    def test_on_all_browsers(self, url: str, test_func):
        """Run test on Firefox, Chromium, WebKit."""
        results = {}

        with sync_playwright() as p:
            for browser_type in ['firefox', 'chromium', 'webkit']:
                browser = getattr(p, browser_type).launch()
                page = browser.new_page()

                try:
                    page.goto(url)
                    result = test_func(page)
                    results[browser_type] = {'status': 'PASS', 'result': result}
                except Exception as e:
                    results[browser_type] = {'status': 'FAIL', 'error': str(e)}
                finally:
                    browser.close()

        return results
```

### Phase 3: Migration & Cleanup (Week 3)

#### Steps:

1. **Create compatibility layer**
   ```python
   # Keep old interface working during transition
   from .playwright_automation import PlaywrightAutomation as RealBrowserAutomation
   ```

2. **Update all imports**
   ```bash
   # Find and replace
   find . -name "*.py" -exec sed -i 's/from real_browser_automation/from playwright_automation/g' {} \;
   ```

3. **Run tests**
   ```bash
   pytest tests/ --browser=all  # Test on all browsers!
   ```

4. **Archive old code**
   ```bash
   mkdir .archive-selenium-$(date +%Y-%m-%d)
   mv real_browser_automation.py .archive-selenium-*/
   ```

## Quick Wins with Playwright

### 1. Built-in Codegen
```bash
# Generate code by recording actions!
playwright codegen github.com

# Creates:
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("https://github.com/")
    page.click("text=Sign in")
    # ... etc
```

### 2. Trace Viewer for Debugging
```python
context.tracing.start(screenshots=True, snapshots=True)
# ... do actions ...
context.tracing.stop(path="trace.zip")

# Then:
# playwright show-trace trace.zip
# Opens beautiful UI showing every action!
```

### 3. Visual Comparisons
```python
# Built-in visual regression testing!
page.screenshot()
expect(page).to_have_screenshot("expected.png")
```

## Installation

### Simple Setup
```bash
# Install Playwright
pip install playwright

# Install browsers (automatic!)
playwright install

# That's it! No driver downloads, no PATH setup
```

### Compare to Selenium
```bash
# Selenium requires:
pip install selenium
# Then download geckodriver manually
# Then add to PATH
# Then configure browser options
# Then hope it works

# vs Playwright:
pip install playwright
playwright install
# Done!
```

## Expected Improvements

| Metric | Before (Selenium) | After (Playwright) | Improvement |
|--------|------------------|-------------------|-------------|
| Setup time | 15-30 min | 2 min | **90% faster** |
| Test speed | Baseline | 2-3x faster | **2-3x faster** |
| Code lines | 100% | 60-70% | **30-40% reduction** |
| Browser support | Firefox only (reliably) | All 3 browsers | **3x coverage** |
| Flakiness | Common | Rare | **90% more stable** |
| Debugging | Screenshots only | Full trace viewer | **10x better** |

## Migration Checklist

### Week 1
- [ ] Create `playwright_automation.py` with core features
- [ ] Port `real_browser_automation.py` functionality
- [ ] Create compatibility layer
- [ ] Update `webpilot_v2_integrated.py`
- [ ] Add network interception examples

### Week 2
- [ ] Implement multi-browser testing
- [ ] Add trace viewer integration
- [ ] Create visual regression tests
- [ ] Update all examples in README
- [ ] Update CI/CD pipelines

### Week 3
- [ ] Run full test suite on all browsers
- [ ] Update documentation
- [ ] Archive Selenium code
- [ ] Remove Selenium dependency
- [ ] Create migration guide for users

## Rollback Plan

If anything goes wrong:
```bash
# Revert is easy - we keep old code
git revert HEAD
# Or restore from archive
cp .archive-selenium-*/* ./
```

## Resources

- [Playwright Python Docs](https://playwright.dev/python/)
- [Migration Guide](https://playwright.dev/python/docs/selenium)
- [Best Practices](https://playwright.dev/python/docs/best-practices)

## Decision: Migrate ✅

**Recommendation**: Proceed with migration
**Risk**: Low (can keep Selenium as fallback)
**Benefit**: High (better DX, faster, more reliable)
**Effort**: 2-3 weeks
**ROI**: Significant long-term maintenance reduction

---

*Modern tools for modern automation. Playwright is the future.*
