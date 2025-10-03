#!/usr/bin/env python3
"""
Unified WebPilot Interface - Playwright Backend
Drop-in replacement for webpilot_v2_integrated.py with better performance.

This provides the same high-level interface but uses Playwright internally.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from .playwright_automation import PlaywrightAutomation
import json
import time


class WebPilot:
    """
    Unified WebPilot interface with Playwright backend.
    Provides the same API as before but with improved performance and reliability.
    """

    def __init__(
        self,
        browser: str = 'firefox',
        headless: bool = True,
        slow_mo: int = 0
    ):
        """
        Initialize WebPilot with Playwright backend.

        Args:
            browser: 'firefox', 'chromium', or 'webkit'
            headless: Run without GUI
            slow_mo: Slow down operations (debugging)
        """
        self.browser_type = browser
        self.headless = headless
        self.slow_mo = slow_mo
        self.automation: Optional[PlaywrightAutomation] = None
        self.results_dir = Path("results")
        self.results_dir.mkdir(exist_ok=True)

    def check_website_status(self, urls: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Check if websites are accessible (core WebPilot feature).

        Args:
            urls: List of URLs to check

        Returns:
            Dictionary with status for each URL
        """
        results = {}

        # Start browser
        self.automation = PlaywrightAutomation(
            browser_type=self.browser_type,
            headless=self.headless,
            slow_mo=self.slow_mo
        )

        if not self.automation.start():
            return {url: {'status': 'ERROR', 'error': 'Failed to start browser'} for url in urls}

        # Check each URL
        for url in urls:
            try:
                print(f"\n🔍 Checking {url}...")

                # Navigate
                success = self.automation.navigate(url)

                if success:
                    # Get page info
                    title = self.automation.get_title()
                    current_url = self.automation.get_url()

                    # Take screenshot for proof
                    clean_name = url.replace('https://', '').replace('http://', '').replace('/', '_')
                    screenshot = self.automation.screenshot(clean_name)

                    # Get basic page stats
                    stats = self.automation.execute_script("""() => ({
                        links: document.querySelectorAll('a').length,
                        images: document.querySelectorAll('img').length,
                        scripts: document.querySelectorAll('script').length
                    })""")

                    results[url] = {
                        'status': 'UP',
                        'title': title,
                        'url': current_url,
                        'screenshot': str(screenshot) if screenshot else None,
                        'stats': stats or {},
                        'timestamp': time.time()
                    }

                    print(f"  ✅ {url} is UP - Title: {title[:50]}...")

                else:
                    results[url] = {
                        'status': 'DOWN',
                        'error': 'Failed to navigate',
                        'timestamp': time.time()
                    }
                    print(f"  ❌ {url} is DOWN")

            except Exception as e:
                results[url] = {
                    'status': 'ERROR',
                    'error': str(e),
                    'timestamp': time.time()
                }
                print(f"  ❌ {url} ERROR: {e}")

        # Close browser
        self.automation.close()

        # Save results
        results_file = self.results_dir / 'site_status.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\n📊 Results saved to {results_file}")
        return results

    def test_web_app(self, url: str, test_sequence: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run automated tests on a web application.

        Args:
            url: Base URL of the application
            test_sequence: List of test actions
                [
                    {"action": "navigate", "url": "..."},
                    {"action": "click", "selector": "..."},
                    {"action": "type", "selector": "...", "text": "..."},
                    {"action": "verify", "selector": "...", "text": "..."}
                ]

        Returns:
            Test results
        """
        self.automation = PlaywrightAutomation(
            browser_type=self.browser_type,
            headless=self.headless,
            slow_mo=self.slow_mo
        )

        if not self.automation.start():
            return {'status': 'ERROR', 'error': 'Failed to start browser'}

        results = {
            'url': url,
            'total_tests': len(test_sequence),
            'passed': 0,
            'failed': 0,
            'details': []
        }

        try:
            # Navigate to base URL
            self.automation.navigate(url)

            # Execute test sequence
            for i, test in enumerate(test_sequence, 1):
                action = test.get('action')
                test_result = {
                    'step': i,
                    'action': action,
                    'status': 'PENDING'
                }

                try:
                    if action == 'navigate':
                        success = self.automation.navigate(test['url'])
                        test_result['status'] = 'PASS' if success else 'FAIL'

                    elif action == 'click':
                        success = self.automation.click(test['selector'])
                        test_result['status'] = 'PASS' if success else 'FAIL'

                    elif action == 'type':
                        success = self.automation.type_text(test['selector'], test['text'])
                        test_result['status'] = 'PASS' if success else 'FAIL'

                    elif action == 'verify':
                        text = self.automation.get_text(test.get('selector'))
                        expected = test.get('text', '')
                        if expected in text:
                            test_result['status'] = 'PASS'
                        else:
                            test_result['status'] = 'FAIL'
                            test_result['error'] = f"Expected '{expected}' not found"

                    elif action == 'screenshot':
                        screenshot = self.automation.screenshot(test.get('name', f'test_step_{i}'))
                        test_result['status'] = 'PASS' if screenshot else 'FAIL'
                        test_result['screenshot'] = str(screenshot) if screenshot else None

                    elif action == 'wait':
                        success = self.automation.wait_for(test['selector'], timeout=test.get('timeout', 5000))
                        test_result['status'] = 'PASS' if success else 'FAIL'

                    else:
                        test_result['status'] = 'FAIL'
                        test_result['error'] = f"Unknown action: {action}"

                    if test_result['status'] == 'PASS':
                        results['passed'] += 1
                    else:
                        results['failed'] += 1

                except Exception as e:
                    test_result['status'] = 'FAIL'
                    test_result['error'] = str(e)
                    results['failed'] += 1

                results['details'].append(test_result)

        except Exception as e:
            results['error'] = str(e)

        finally:
            self.automation.close()

        results['success_rate'] = (results['passed'] / results['total_tests'] * 100) if results['total_tests'] > 0 else 0

        # Save results
        results_file = self.results_dir / 'test_results.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)

        return results

    def extract_data(self, url: str, selectors: Dict[str, str]) -> Dict[str, Any]:
        """
        Extract structured data from a webpage.

        Args:
            url: URL to scrape
            selectors: Dictionary of {field_name: selector}

        Returns:
            Extracted data
        """
        self.automation = PlaywrightAutomation(
            browser_type=self.browser_type,
            headless=self.headless
        )

        if not self.automation.start():
            return {'error': 'Failed to start browser'}

        try:
            # Navigate
            self.automation.navigate(url)

            # Extract data
            data = {
                'url': url,
                'title': self.automation.get_title(),
                'timestamp': time.time(),
                'fields': {}
            }

            for field_name, selector in selectors.items():
                try:
                    elements = self.automation.get_elements(selector)
                    if len(elements) == 1:
                        data['fields'][field_name] = self.automation.get_text(selector)
                    else:
                        # Multiple elements - return list
                        data['fields'][field_name] = [
                            elem.text_content() for elem in elements
                        ]
                except Exception as e:
                    data['fields'][field_name] = None
                    data.setdefault('errors', {})[field_name] = str(e)

            return data

        finally:
            self.automation.close()

    def monitor_changes(
        self,
        url: str,
        selector: str,
        interval: int = 60,
        duration: int = 300
    ) -> List[Dict[str, Any]]:
        """
        Monitor element for changes over time.

        Args:
            url: URL to monitor
            selector: Element selector
            interval: Check interval in seconds
            duration: Total monitoring duration in seconds

        Returns:
            List of change records
        """
        self.automation = PlaywrightAutomation(
            browser_type=self.browser_type,
            headless=self.headless
        )

        if not self.automation.start():
            return [{'error': 'Failed to start browser'}]

        changes = []
        previous_text = None
        start_time = time.time()

        try:
            self.automation.navigate(url)

            while (time.time() - start_time) < duration:
                current_text = self.automation.get_text(selector)

                if current_text != previous_text:
                    changes.append({
                        'timestamp': time.time(),
                        'text': current_text,
                        'changed': previous_text is not None
                    })
                    previous_text = current_text

                    if len(changes) > 1:
                        print(f"🔄 Change detected at {selector}")

                time.sleep(interval)

                # Reload page
                self.automation.reload()

        finally:
            self.automation.close()

        return changes


# Backward compatibility aliases
class RealBrowserAutomation(PlaywrightAutomation):
    """
    Backward compatibility alias.
    Existing code using RealBrowserAutomation will now use Playwright!
    """
    pass


# Example usage
if __name__ == "__main__":
    print("🚀 WebPilot Unified Interface Demo\n")

    # Example 1: Website monitoring
    pilot = WebPilot(headless=True)
    results = pilot.check_website_status([
        "github.com",
        "stackoverflow.com",
        "python.org"
    ])

    print("\n📊 Monitoring Results:")
    for url, status in results.items():
        print(f"  {url}: {status['status']}")

    # Example 2: Web app testing
    test_sequence = [
        {"action": "navigate", "url": "https://github.com"},
        {"action": "screenshot", "name": "github_home"},
        {"action": "verify", "text": "GitHub"},
        {"action": "click", "selector": "text=Sign in"},
        {"action": "screenshot", "name": "github_login"}
    ]

    print("\n🧪 Running Web App Tests...")
    test_results = pilot.test_web_app("https://github.com", test_sequence)
    print(f"  Tests passed: {test_results['passed']}/{test_results['total_tests']}")
    print(f"  Success rate: {test_results['success_rate']:.1f}%")

    print("\n✨ Demo complete! Check results/ folder for outputs.")
