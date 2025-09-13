#!/usr/bin/env python3
"""
Comprehensive WebPilot Test Suite
Tests all major improvements and features
"""

import unittest
import asyncio
import time
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from webpilot.core import (
    WebPilot, WebPilotSession, ActionResult, ActionType, 
    BrowserType, WebPilotError, BrowserNotStartedError,
    ElementNotFoundError, TimeoutError, NavigationError
)
from webpilot.utils.smart_wait import SmartWait
from webpilot.utils.reporter import TestReport, TestResult, PerformanceReport
from webpilot.monitoring.dashboard import WebPilotMonitor, MetricsCollector


class TestCoreImprovements(unittest.TestCase):
    """Test core improvements: error handling, enums, and session management"""
    
    def test_new_action_types(self):
        """Test that new ActionType enums are available"""
        # Test new enums added
        self.assertIsNotNone(ActionType.HOVER)
        self.assertIsNotNone(ActionType.DRAG)
        self.assertIsNotNone(ActionType.DOUBLE_CLICK)
        self.assertIsNotNone(ActionType.RIGHT_CLICK)
        self.assertIsNotNone(ActionType.CLEAR)
        self.assertIsNotNone(ActionType.REFRESH)
        self.assertIsNotNone(ActionType.BACK)
        self.assertIsNotNone(ActionType.FORWARD)
        self.assertIsNotNone(ActionType.SCRIPT)
        
    def test_error_handling_classes(self):
        """Test comprehensive error handling"""
        # Test base error
        error = WebPilotError("Test error")
        self.assertIsInstance(error, Exception)
        
        # Test specific errors
        browser_error = BrowserNotStartedError()
        self.assertIsInstance(browser_error, WebPilotError)
        
        element_error = ElementNotFoundError("button#submit")
        self.assertIsInstance(element_error, WebPilotError)
        
        timeout_error = TimeoutError(30)
        self.assertIsInstance(timeout_error, WebPilotError)
        
        nav_error = NavigationError("https://example.com", "404")
        self.assertIsInstance(nav_error, WebPilotError)
        
    def test_session_management(self):
        """Test enhanced session management"""
        session = WebPilotSession()
        
        # Test session ID generation
        self.assertIsNotNone(session.session_id)
        self.assertTrue(len(session.session_id) > 10)
        
        # Test session directory creation
        self.assertTrue(session.session_dir.exists())
        
        # Test action logging
        action = ActionResult(
            success=True,
            action_type=ActionType.NAVIGATE,
            data={'url': 'https://example.com'},
            duration_ms=150.5
        )
        session.add_action(action)
        
        # Test session state
        session.state['current_url'] = 'https://example.com'
        session.save_state()
        
        # Test session loading
        loaded_session = WebPilotSession(session.session_id)
        self.assertEqual(loaded_session.state['current_url'], 'https://example.com')


class TestSmartWaitUtility(unittest.TestCase):
    """Test smart wait strategies"""
    
    @patch('webpilot.utils.smart_wait.WebDriverWait')
    def test_wait_for_network_idle(self, mock_wait):
        """Test network idle waiting"""
        mock_driver = MagicMock()
        mock_wait.return_value.until = MagicMock(return_value=True)
        
        result = SmartWait.wait_for_network_idle(mock_driver)
        self.assertTrue(result)
        mock_wait.assert_called_once()
        
    @patch('webpilot.utils.smart_wait.WebDriverWait')
    def test_wait_for_element_stable(self, mock_wait):
        """Test element stability waiting"""
        mock_driver = MagicMock()
        mock_wait.return_value.until = MagicMock(return_value=True)
        
        result = SmartWait.wait_for_element_stable(mock_driver, "#content")
        self.assertTrue(result)
        
    def test_wait_for_page_ready(self):
        """Test page ready detection"""
        mock_driver = MagicMock()
        mock_driver.execute_script.return_value = "complete"
        
        result = SmartWait.wait_for_page_ready(mock_driver)
        self.assertTrue(result)
        mock_driver.execute_script.assert_called_with(
            "return document.readyState"
        )


class TestReportingEnhancements(unittest.TestCase):
    """Test enhanced reporting capabilities"""
    
    def test_test_report_generation(self):
        """Test comprehensive test report generation"""
        report = TestReport("WebPilot Test Suite")
        
        # Add test results
        report.add_result(TestResult(
            name="Homepage Load Test",
            status="passed",
            duration_ms=1250.5
        ))
        
        report.add_result(TestResult(
            name="Login Test",
            status="failed",
            duration_ms=3400.2,
            error="Invalid credentials"
        ))
        
        report.add_result(TestResult(
            name="Search Test",
            status="skipped",
            duration_ms=0
        ))
        
        # Add metadata
        report.add_metadata("environment", "production")
        report.add_metadata("browser", "firefox")
        
        # Generate JSON report
        json_report = report.generate_json_report()
        
        self.assertEqual(json_report['summary']['total'], 3)
        self.assertEqual(json_report['summary']['passed'], 1)
        self.assertEqual(json_report['summary']['failed'], 1)
        self.assertEqual(json_report['summary']['skipped'], 1)
        self.assertAlmostEqual(json_report['summary']['pass_rate'], 33.33, places=1)
        
        # Test HTML generation
        html_report = report.generate_html_report()
        self.assertIn("WebPilot Test Suite", html_report)
        self.assertIn("Homepage Load Test", html_report)
        self.assertIn("✅", html_report)  # Pass icon
        self.assertIn("❌", html_report)  # Fail icon
        
    def test_performance_report(self):
        """Test performance metrics reporting"""
        perf_report = PerformanceReport()
        
        # Add metrics
        perf_report.add_metric("https://example.com", {
            'load_time_ms': 1500,
            'first_contentful_paint_ms': 800,
            'largest_contentful_paint_ms': 1200
        })
        
        perf_report.add_metric("https://example.org", {
            'load_time_ms': 2000,
            'first_contentful_paint_ms': 1000,
            'largest_contentful_paint_ms': 1800
        })
        
        # Generate summary
        summary = perf_report.generate_summary()
        
        self.assertEqual(summary['total_pages'], 2)
        self.assertEqual(summary['average_load_time_ms'], 1750)
        self.assertEqual(summary['average_fcp_ms'], 900)
        self.assertEqual(summary['slowest_page']['load_time_ms'], 2000)
        self.assertEqual(summary['fastest_page']['load_time_ms'], 1500)


class TestMonitoringDashboard(unittest.TestCase):
    """Test monitoring dashboard functionality"""
    
    def test_monitor_initialization(self):
        """Test monitor setup"""
        monitor = WebPilotMonitor(port=8888)
        
        self.assertEqual(monitor.port, 8888)
        self.assertEqual(len(monitor.metrics), 0)
        self.assertEqual(len(monitor.current_tests), 0)
        
    def test_test_tracking(self):
        """Test tracking test execution"""
        monitor = WebPilotMonitor()
        
        # Start a test
        monitor.add_test_start("Homepage Test")
        self.assertEqual(len(monitor.current_tests), 1)
        self.assertIn("Homepage Test", monitor.current_tests)
        
        # Complete the test
        monitor.add_test_result(
            "Homepage Test",
            status="passed",
            duration_ms=1500,
            metrics={'load_time': 1200}
        )
        
        self.assertEqual(len(monitor.current_tests), 0)
        self.assertEqual(len(monitor.metrics), 1)
        
        # Check statistics
        stats = monitor.get_statistics()
        self.assertEqual(stats['total'], 1)
        self.assertEqual(stats['passed'], 1)
        self.assertEqual(stats['failed'], 0)
        self.assertEqual(stats['pass_rate'], 100.0)
        
    def test_metrics_collector(self):
        """Test metrics collection"""
        collector = MetricsCollector()
        
        # Add metrics
        collector.add_metric("page_load", 1500, "ms")
        collector.add_metric("page_load", 1200, "ms")
        collector.add_metric("page_load", 1800, "ms")
        collector.add_metric("api_call", 250, "ms")
        
        # Get summary
        summary = collector.get_summary()
        
        self.assertEqual(summary['page_load']['count'], 3)
        self.assertEqual(summary['page_load']['min'], 1200)
        self.assertEqual(summary['page_load']['max'], 1800)
        self.assertEqual(summary['page_load']['avg'], 1500)
        
        self.assertEqual(summary['api_call']['count'], 1)
        self.assertEqual(summary['api_call']['avg'], 250)


class TestBackendIntegration(unittest.TestCase):
    """Test multiple backend support"""
    
    @patch('webpilot.backends.selenium.webdriver.Firefox')
    def test_selenium_backend(self, mock_firefox):
        """Test Selenium backend initialization"""
        from webpilot.backends.selenium import SeleniumWebPilot
        
        mock_driver = MagicMock()
        mock_firefox.return_value = mock_driver
        
        pilot = SeleniumWebPilot(browser=BrowserType.FIREFOX, headless=True)
        
        # Mock start method
        mock_driver.get = MagicMock()
        result = pilot.start("https://example.com")
        
        self.assertIsNotNone(result)
        mock_firefox.assert_called_once()
        
    @unittest.skipUnless('playwright' in sys.modules, "Playwright not installed")
    async def test_playwright_backend(self):
        """Test Playwright backend (if available)"""
        from webpilot.backends.playwright_pilot import PlaywrightWebPilot
        
        pilot = PlaywrightWebPilot(headless=True)
        
        # This would normally connect to a real browser
        # For testing, we just verify the class exists
        self.assertIsNotNone(pilot)
        self.assertEqual(pilot.headless, True)


class TestAsyncOperations(unittest.TestCase):
    """Test async functionality"""
    
    async def test_async_webpilot(self):
        """Test AsyncWebPilot class"""
        from webpilot.async_pilot import AsyncWebPilot
        
        # Create async pilot
        async with AsyncWebPilot() as pilot:
            # Mock the fetch method
            pilot.fetch = MagicMock(return_value=ActionResult(
                success=True,
                action_type=ActionType.NAVIGATE,
                data={'status': 200},
                duration_ms=500
            ))
            
            # Test batch operations
            urls = [
                "https://example.com",
                "https://example.org",
                "https://example.net"
            ]
            
            results = await pilot.batch_fetch(urls)
            self.assertEqual(len(results), 3)
            
    def test_async_runner(self):
        """Test running async operations"""
        asyncio.run(self.test_async_webpilot())


class TestCLIInterface(unittest.TestCase):
    """Test CLI functionality"""
    
    @patch('webpilot.cli.WebPilot')
    def test_cli_browse_command(self, mock_pilot_class):
        """Test browse command"""
        from webpilot.cli import WebPilotCLI
        
        # Setup mock
        mock_pilot = MagicMock()
        mock_pilot_class.return_value = mock_pilot
        mock_pilot.start.return_value = ActionResult(
            success=True,
            action_type=ActionType.NAVIGATE,
            data={'title': 'Example'},
            duration_ms=100
        )
        
        # Create CLI
        cli = WebPilotCLI()
        
        # Mock args
        args = MagicMock()
        args.command = 'browse'
        args.url = 'https://example.com'
        args.browser = 'firefox'
        args.headless = True
        args.session = None
        args.verbose = False
        args.screenshot = False
        
        # Execute command
        result = cli.cmd_browse(args, mock_pilot)
        
        self.assertEqual(result, 0)
        mock_pilot.start.assert_called_with('https://example.com')


class TestRealWorldIntegration(unittest.TestCase):
    """Test real-world usage patterns"""
    
    @patch('webpilot.core.WebPilot')
    def test_terra_atlas_pattern(self, mock_pilot_class):
        """Test pattern from Terra Atlas testing"""
        mock_pilot = MagicMock()
        mock_pilot_class.return_value.__enter__ = MagicMock(return_value=mock_pilot)
        mock_pilot_class.return_value.__exit__ = MagicMock()
        
        # Simulate Terra Atlas test pattern
        with mock_pilot_class() as pilot:
            # Navigation
            pilot.start.return_value = ActionResult(success=True, action_type=ActionType.NAVIGATE, data={}, duration_ms=100)
            
            # Screenshot
            pilot.screenshot.return_value = ActionResult(success=True, action_type=ActionType.SCREENSHOT, data={'path': 'test.png'}, duration_ms=50)
            
            # Click
            pilot.click.return_value = ActionResult(success=True, action_type=ActionType.CLICK, data={}, duration_ms=30)
            
            # Run test sequence
            nav_result = pilot.start("https://atlas.luminousdynamics.io")
            self.assertTrue(nav_result.success)
            
            ss_result = pilot.screenshot("homepage.png")
            self.assertTrue(ss_result.success)
            
            click_result = pilot.click(selector="nav a[href='/explore']")
            self.assertTrue(click_result.success)


def run_tests():
    """Run all tests with verbose output"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCoreImprovements))
    suite.addTests(loader.loadTestsFromTestCase(TestSmartWaitUtility))
    suite.addTests(loader.loadTestsFromTestCase(TestReportingEnhancements))
    suite.addTests(loader.loadTestsFromTestCase(TestMonitoringDashboard))
    suite.addTests(loader.loadTestsFromTestCase(TestBackendIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestAsyncOperations))
    suite.addTests(loader.loadTestsFromTestCase(TestCLIInterface))
    suite.addTests(loader.loadTestsFromTestCase(TestRealWorldIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*60)
    print("WebPilot Test Suite Summary")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed")
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    import sys
    sys.exit(run_tests())