#!/usr/bin/env python3
"""
Terra Atlas Performance and Functionality Testing
Real-world example of WebPilot for production site testing
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from webpilot import WebPilotDevOps, AsyncWebPilot
from webpilot.utils import TestReport, TestResult, SmartWait
from webpilot.backends.selenium import SeleniumWebPilot
from webpilot.backends.playwright_pilot import PlaywrightWebPilot

# Terra Atlas URLs
BASE_URL = "https://atlas.luminousdynamics.io"
PAGES = [
    "/",
    "/explore",
    "/invest",
    "/about",
    "/contact"
]


class TerraAtlasTestSuite:
    """Comprehensive test suite for Terra Atlas platform"""
    
    def __init__(self):
        self.report = TestReport("Terra Atlas Test Report")
        self.devops = WebPilotDevOps(headless=True)
        
    async def test_performance(self):
        """Test page load performance for all pages"""
        print("🚀 Testing Performance...")
        
        for page in PAGES:
            url = BASE_URL + page
            start = datetime.now()
            
            try:
                # Use DevOps tool for performance audit
                perf = self.devops.performance_audit(url)
                
                # Check performance thresholds
                passed = (
                    perf.load_time_ms < 3000 and
                    perf.first_contentful_paint_ms < 1500 and
                    perf.largest_contentful_paint_ms < 2500
                )
                
                result = TestResult(
                    name=f"Performance: {page}",
                    status='passed' if passed else 'failed',
                    duration_ms=(datetime.now() - start).total_seconds() * 1000,
                    error=None if passed else f"Load time: {perf.load_time_ms}ms (threshold: 3000ms)"
                )
                
                self.report.add_result(result)
                
                # Add performance metrics to report
                self.report.add_metadata(f"perf_{page}", {
                    'load_time_ms': perf.load_time_ms,
                    'fcp_ms': perf.first_contentful_paint_ms,
                    'lcp_ms': perf.largest_contentful_paint_ms
                })
                
                print(f"  {page}: {'✅' if passed else '❌'} Load: {perf.load_time_ms}ms, FCP: {perf.first_contentful_paint_ms}ms")
                
            except Exception as e:
                result = TestResult(
                    name=f"Performance: {page}",
                    status='failed',
                    duration_ms=(datetime.now() - start).total_seconds() * 1000,
                    error=str(e)
                )
                self.report.add_result(result)
                print(f"  {page}: ❌ Error: {e}")
    
    async def test_accessibility(self):
        """Test accessibility compliance"""
        print("\n♿ Testing Accessibility...")
        
        for page in PAGES[:2]:  # Test main pages
            url = BASE_URL + page
            start = datetime.now()
            
            try:
                # Run accessibility audit
                a11y = self.devops.accessibility_check(url)
                
                passed = a11y.score >= 90
                
                result = TestResult(
                    name=f"Accessibility: {page}",
                    status='passed' if passed else 'failed',
                    duration_ms=(datetime.now() - start).total_seconds() * 1000,
                    error=None if passed else f"Score: {a11y.score}/100 (threshold: 90)"
                )
                
                self.report.add_result(result)
                
                print(f"  {page}: {'✅' if passed else '❌'} Score: {a11y.score}/100")
                
                if a11y.issues:
                    print(f"    Issues: {len(a11y.issues)}")
                    for issue in a11y.issues[:3]:  # Show first 3 issues
                        print(f"      - {issue.get('description', 'Unknown issue')}")
                
            except Exception as e:
                result = TestResult(
                    name=f"Accessibility: {page}",
                    status='failed',
                    duration_ms=(datetime.now() - start).total_seconds() * 1000,
                    error=str(e)
                )
                self.report.add_result(result)
                print(f"  {page}: ❌ Error: {e}")
    
    async def test_smoke_tests(self):
        """Run smoke tests on all URLs"""
        print("\n🔥 Running Smoke Tests...")
        
        urls = [BASE_URL + page for page in PAGES]
        results = await self.devops.smoke_test(urls)
        
        self.report.add_metadata('smoke_test_summary', results)
        
        print(f"  Total URLs: {results['total']}")
        print(f"  Passed: {results['passed']} ✅")
        print(f"  Failed: {results['failed']} ❌")
        
        if results['failures']:
            print("  Failed URLs:")
            for failure in results['failures']:
                print(f"    - {failure['url']}: {failure.get('error', 'Unknown error')}")
    
    def test_interactive_elements(self):
        """Test interactive elements with Selenium"""
        print("\n🎯 Testing Interactive Elements...")
        
        with SeleniumWebPilot(headless=True) as pilot:
            start = datetime.now()
            
            try:
                # Navigate to homepage
                result = pilot.start(BASE_URL)
                if not result.success:
                    raise Exception(f"Failed to load homepage: {result.error}")
                
                # Wait for page to be ready
                SmartWait.wait_for_page_ready(pilot.driver)
                
                # Take screenshot for visual validation
                screenshot_result = pilot.screenshot("terra_atlas_homepage.png")
                
                # Test navigation menu
                menu_test = pilot.click(selector="nav a[href='/explore']")
                
                # Check if navigation worked
                current_url = pilot.driver.current_url
                nav_passed = '/explore' in current_url
                
                test_result = TestResult(
                    name="Interactive: Navigation Menu",
                    status='passed' if nav_passed else 'failed',
                    duration_ms=(datetime.now() - start).total_seconds() * 1000,
                    screenshot=screenshot_result.data.get('path') if screenshot_result.success else None
                )
                
                self.report.add_result(test_result)
                
                print(f"  Navigation Menu: {'✅' if nav_passed else '❌'}")
                
                # Test search functionality if present
                try:
                    search_input = pilot.driver.find_element_by_css_selector("input[type='search'], input[placeholder*='Search']")
                    if search_input:
                        pilot.type_text(search_input, "renewable energy")
                        pilot.submit()
                        print(f"  Search Function: ✅")
                except:
                    print(f"  Search Function: ⏭️  (Not found)")
                
            except Exception as e:
                result = TestResult(
                    name="Interactive: Elements Test",
                    status='failed',
                    duration_ms=(datetime.now() - start).total_seconds() * 1000,
                    error=str(e)
                )
                self.report.add_result(result)
                print(f"  Interactive Elements: ❌ Error: {e}")
    
    async def test_api_endpoints(self):
        """Test API endpoints if available"""
        print("\n🌐 Testing API Endpoints...")
        
        api_endpoints = [
            "/api/health",
            "/api/sites",
            "/api/stats"
        ]
        
        async with AsyncWebPilot() as pilot:
            for endpoint in api_endpoints:
                url = BASE_URL + endpoint
                start = datetime.now()
                
                try:
                    result = await pilot.fetch(url)
                    
                    passed = result.success and result.data.get('status', 0) in [200, 404]
                    
                    test_result = TestResult(
                        name=f"API: {endpoint}",
                        status='passed' if passed else 'failed',
                        duration_ms=(datetime.now() - start).total_seconds() * 1000,
                        error=None if passed else f"Status: {result.data.get('status', 'Unknown')}"
                    )
                    
                    self.report.add_result(test_result)
                    
                    print(f"  {endpoint}: {'✅' if passed else '❌'} Status: {result.data.get('status', 'N/A')}")
                    
                except Exception as e:
                    test_result = TestResult(
                        name=f"API: {endpoint}",
                        status='failed',
                        duration_ms=(datetime.now() - start).total_seconds() * 1000,
                        error=str(e)
                    )
                    self.report.add_result(test_result)
                    print(f"  {endpoint}: ❌ Error: {e}")
    
    async def run_all_tests(self):
        """Run complete test suite"""
        print("=" * 60)
        print("🚁 Terra Atlas Test Suite - WebPilot")
        print("=" * 60)
        
        # Add metadata
        self.report.add_metadata('test_environment', 'production')
        self.report.add_metadata('base_url', BASE_URL)
        self.report.add_metadata('timestamp', datetime.now().isoformat())
        
        # Run tests
        await self.test_performance()
        await self.test_accessibility()
        await self.test_smoke_tests()
        self.test_interactive_elements()
        await self.test_api_endpoints()
        
        # Generate and save report
        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)
        
        stats = self.report.generate_json_report()['summary']
        print(f"Total Tests: {stats['total']}")
        print(f"Passed: {stats['passed']} ✅")
        print(f"Failed: {stats['failed']} ❌")
        print(f"Skipped: {stats['skipped']} ⏭️")
        print(f"Pass Rate: {stats['pass_rate']:.1f}%")
        
        # Save reports
        report_dir = Path(__file__).parent / 'reports'
        report_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = report_dir / f'terra_atlas_report_{timestamp}'
        
        self.report.save_report(report_path, format='both')
        
        print(f"\n📁 Reports saved to:")
        print(f"  - {report_path}.html")
        print(f"  - {report_path}.json")
        
        return stats['pass_rate'] >= 80  # Return True if 80% or more tests pass


async def main():
    """Main test runner"""
    suite = TerraAtlasTestSuite()
    success = await suite.run_all_tests()
    
    # Exit with appropriate code for CI/CD
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())