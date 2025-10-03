#!/usr/bin/env python3
"""
Multi-Browser Testing - Playwright Advantage
Test on Firefox, Chrome, and Safari with the same code!
"""

from typing import List, Dict, Any, Callable, Optional
from playwright.sync_api import sync_playwright, Page
import time
import json
from pathlib import Path


class MultiBrowserTester:
    """
    Run tests across multiple browsers simultaneously.
    This is one of Playwright's killer features!
    """

    def __init__(self, browsers: Optional[List[str]] = None, headless: bool = True):
        """
        Initialize multi-browser tester.

        Args:
            browsers: List of browsers ('firefox', 'chromium', 'webkit')
                     If None, tests on all three
            headless: Run without GUI
        """
        self.browsers = browsers or ['firefox', 'chromium', 'webkit']
        self.headless = headless
        self.results_dir = Path("multi_browser_results")
        self.results_dir.mkdir(exist_ok=True)

    def test_url_on_all_browsers(self, url: str) -> Dict[str, Dict[str, Any]]:
        """
        Load URL on all browsers and collect results.

        Args:
            url: URL to test

        Returns:
            Results for each browser
        """
        results = {}

        with sync_playwright() as p:
            for browser_name in self.browsers:
                print(f"\n🌐 Testing on {browser_name}...")

                try:
                    # Launch browser
                    browser_launcher = getattr(p, browser_name)
                    browser = browser_launcher.launch(headless=self.headless)
                    page = browser.new_page()

                    # Navigate
                    start_time = time.time()
                    page.goto(url)
                    load_time = time.time() - start_time

                    # Collect data
                    results[browser_name] = {
                        'status': 'SUCCESS',
                        'load_time': load_time,
                        'title': page.title(),
                        'url': page.url,
                        'viewport': page.viewport_size,
                        'stats': page.evaluate("""() => ({
                            links: document.querySelectorAll('a').length,
                            images: document.querySelectorAll('img').length,
                            scripts: document.querySelectorAll('script').length
                        })""")
                    }

                    # Take screenshot
                    screenshot_path = self.results_dir / f"{browser_name}_screenshot.png"
                    page.screenshot(path=str(screenshot_path))
                    results[browser_name]['screenshot'] = str(screenshot_path)

                    print(f"  ✅ {browser_name}: {load_time:.2f}s load time")

                    browser.close()

                except Exception as e:
                    results[browser_name] = {
                        'status': 'FAILED',
                        'error': str(e)
                    }
                    print(f"  ❌ {browser_name}: {e}")

        return results

    def run_test_sequence(
        self,
        url: str,
        test_function: Callable[[Page], Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Run custom test function on all browsers.

        Args:
            url: URL to test
            test_function: Function that takes Page and returns test results

        Returns:
            Results for each browser
        """
        results = {}

        with sync_playwright() as p:
            for browser_name in self.browsers:
                print(f"\n🧪 Running test on {browser_name}...")

                try:
                    # Launch browser
                    browser_launcher = getattr(p, browser_name)
                    browser = browser_launcher.launch(headless=self.headless)
                    page = browser.new_page()
                    page.goto(url)

                    # Run test
                    start_time = time.time()
                    test_result = test_function(page)
                    test_time = time.time() - start_time

                    results[browser_name] = {
                        'status': 'SUCCESS',
                        'test_time': test_time,
                        'results': test_result
                    }

                    print(f"  ✅ {browser_name}: Test completed in {test_time:.2f}s")

                    browser.close()

                except Exception as e:
                    results[browser_name] = {
                        'status': 'FAILED',
                        'error': str(e)
                    }
                    print(f"  ❌ {browser_name}: {e}")

        return results

    def compare_rendering(self, url: str) -> Dict[str, str]:
        """
        Take screenshots on all browsers for visual comparison.

        Args:
            url: URL to capture

        Returns:
            Paths to screenshots
        """
        screenshots = {}

        with sync_playwright() as p:
            for browser_name in self.browsers:
                try:
                    browser_launcher = getattr(p, browser_name)
                    browser = browser_launcher.launch(headless=self.headless)
                    page = browser.new_page()
                    page.goto(url)

                    # Full page screenshot
                    screenshot_path = self.results_dir / f"{browser_name}_full_page.png"
                    page.screenshot(path=str(screenshot_path), full_page=True)
                    screenshots[browser_name] = str(screenshot_path)

                    print(f"  📸 {browser_name}: Screenshot saved")

                    browser.close()

                except Exception as e:
                    print(f"  ❌ {browser_name}: {e}")
                    screenshots[browser_name] = f"FAILED: {e}"

        return screenshots

    def test_responsive_design(self, url: str) -> Dict[str, Dict[str, Any]]:
        """
        Test responsive design across multiple viewports.

        Args:
            url: URL to test

        Returns:
            Results for each viewport
        """
        viewports = {
            'mobile': {'width': 375, 'height': 667},
            'tablet': {'width': 768, 'height': 1024},
            'desktop': {'width': 1920, 'height': 1080}
        }

        results = {}

        with sync_playwright() as p:
            # Use chromium for responsive testing
            browser = p.chromium.launch(headless=self.headless)

            for device_name, viewport in viewports.items():
                try:
                    context = browser.new_context(viewport=viewport)
                    page = context.new_page()
                    page.goto(url)

                    # Collect data
                    results[device_name] = {
                        'viewport': viewport,
                        'title': page.title(),
                        'stats': page.evaluate("""() => ({
                            width: window.innerWidth,
                            height: window.innerHeight,
                            scrollHeight: document.body.scrollHeight
                        })""")
                    }

                    # Screenshot
                    screenshot_path = self.results_dir / f"{device_name}_view.png"
                    page.screenshot(path=str(screenshot_path), full_page=True)
                    results[device_name]['screenshot'] = str(screenshot_path)

                    print(f"  📱 {device_name} ({viewport['width']}x{viewport['height']}): OK")

                    context.close()

                except Exception as e:
                    results[device_name] = {'error': str(e)}

            browser.close()

        return results

    def save_results(self, results: Dict, filename: str = "multi_browser_results.json"):
        """Save test results to file."""
        output_path = self.results_dir / filename
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📊 Results saved to {output_path}")


# Example usage
if __name__ == "__main__":
    print("🌐 Multi-Browser Testing Demo\n")

    tester = MultiBrowserTester(headless=False)

    # Test 1: Basic compatibility
    print("=" * 60)
    print("TEST 1: Cross-Browser Compatibility")
    print("=" * 60)

    results = tester.test_url_on_all_browsers("https://example.com")

    print("\n📊 Results:")
    for browser, result in results.items():
        if result['status'] == 'SUCCESS':
            print(f"  {browser:10s}: ✅ Loaded in {result['load_time']:.2f}s")
        else:
            print(f"  {browser:10s}: ❌ {result.get('error', 'Unknown error')}")

    # Test 2: Visual comparison
    print("\n" + "=" * 60)
    print("TEST 2: Visual Rendering Comparison")
    print("=" * 60)

    screenshots = tester.compare_rendering("https://example.com")
    print(f"\n📸 Screenshots saved:")
    for browser, path in screenshots.items():
        print(f"  {browser}: {path}")

    # Test 3: Responsive design
    print("\n" + "=" * 60)
    print("TEST 3: Responsive Design Testing")
    print("=" * 60)

    responsive_results = tester.test_responsive_design("https://example.com")

    # Save all results
    tester.save_results({
        'cross_browser': results,
        'screenshots': screenshots,
        'responsive': responsive_results
    })

    print("\n✨ Multi-browser testing complete!")
    print(f"   Check {tester.results_dir}/ for screenshots and results")
