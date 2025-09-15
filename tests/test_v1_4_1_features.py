#!/usr/bin/env python3
"""
Test suite for WebPilot v1.4.1 features

Tests the new utilities and enhancements:
- Retry mechanisms
- Failure capture
- Smart errors
- Network mocking
"""

import unittest
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from webpilot.utils.retry import retry, retry_with_result, RetryableOperation, with_retry
from webpilot.utils.failure_capture import FailureCapture, capture_on_failure, SmartErrorAnalyzer
from webpilot.utils.smart_errors import (
    SmartElementNotFoundError,
    SmartTimeoutError,
    SmartNetworkError,
    ErrorSuggestionEngine
)
from webpilot.utils.network_mock import (
    NetworkMocker,
    MockResponse,
    MockRule,
    MockStrategy,
    mock_api_endpoints,
    mock_static_assets,
    mock_slow_endpoints
)


class TestRetryMechanisms(unittest.TestCase):
    """Test retry utilities"""
    
    def test_retry_decorator_success_first_try(self):
        """Test retry decorator when function succeeds on first try"""
        call_count = 0
        
        @retry(times=3, delay=0.1)
        def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = successful_function()
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 1)
    
    def test_retry_decorator_success_after_failures(self):
        """Test retry decorator when function succeeds after failures"""
        call_count = 0
        
        @retry(times=3, delay=0.1)
        def eventually_successful():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Not yet")
            return "success"
        
        result = eventually_successful()
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 3)
    
    def test_retry_decorator_all_failures(self):
        """Test retry decorator when all attempts fail"""
        call_count = 0
        
        @retry(times=3, delay=0.1)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")
        
        with self.assertRaises(ValueError):
            always_fails()
        self.assertEqual(call_count, 3)
    
    def test_retry_with_result_predicate(self):
        """Test retry with result predicate"""
        call_count = 0
        
        @retry_with_result(lambda x: x > 5, times=3, delay=0.1)
        def get_number():
            nonlocal call_count
            call_count += 1
            return call_count * 2
        
        result = get_number()
        self.assertEqual(result, 6)  # Third attempt: 3 * 2 = 6
        self.assertEqual(call_count, 3)
    
    def test_retryable_operation_context(self):
        """Test RetryableOperation context manager"""
        attempts = []
        
        with RetryableOperation(times=3, delay=0.1) as retry_op:
            while retry_op.should_retry():
                attempts.append(retry_op.attempt)
                if retry_op.attempt < 3:
                    retry_op.failed()
                else:
                    retry_op.success()
        
        self.assertEqual(attempts, [1, 2, 3])
    
    def test_with_retry_function(self):
        """Test with_retry function wrapper"""
        mock_func = Mock(side_effect=[ValueError("Fail"), ValueError("Fail"), "Success"])
        
        result = with_retry(mock_func, times=3, delay=0.1)
        self.assertEqual(result, "Success")
        self.assertEqual(mock_func.call_count, 3)


class TestFailureCapture(unittest.TestCase):
    """Test failure capture utilities"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.failure_capture = FailureCapture(
            screenshot=True,
            html=True,
            console_logs=True,
            directory=self.temp_dir
        )
    
    def test_failure_capture_initialization(self):
        """Test FailureCapture initialization"""
        self.assertTrue(Path(self.temp_dir).exists())
        self.assertTrue(self.failure_capture.screenshot)
        self.assertTrue(self.failure_capture.html)
        self.assertTrue(self.failure_capture.console_logs)
    
    def test_capture_failure_creates_artifacts(self):
        """Test capture_failure creates artifact files"""
        # Mock pilot object
        mock_pilot = Mock()
        mock_pilot.screenshot = Mock()
        mock_pilot.get_page_source = Mock(return_value="<html>Test</html>")
        mock_pilot.get_console_logs = Mock(return_value=[{"message": "test"}])
        mock_pilot.get_network_logs = Mock(return_value=[{"url": "test.com"}])
        mock_pilot.get_performance_metrics = Mock(return_value={"metric": 123})
        mock_pilot.current_url = "https://example.com"
        
        # Capture failure
        exception = ValueError("Test error")
        artifacts = self.failure_capture.capture_failure(
            mock_pilot, "test_case", exception
        )
        
        # Check artifacts
        self.assertIn("test_name", artifacts)
        self.assertEqual(artifacts["test_name"], "test_case")
        self.assertIn("exception", artifacts)
        self.assertIn("directory", artifacts)
        
        # Check directory was created
        test_dir = Path(artifacts["directory"])
        self.assertTrue(test_dir.exists())
    
    def test_capture_on_failure_decorator(self):
        """Test capture_on_failure decorator"""
        mock_pilot = Mock()
        mock_pilot.screenshot = Mock()
        
        @capture_on_failure(self.failure_capture)
        def failing_test(pilot):
            raise ValueError("Test failure")
        
        with self.assertRaises(ValueError) as cm:
            failing_test(mock_pilot)
        
        # Check that failure_artifacts was added to exception
        self.assertTrue(hasattr(cm.exception, 'failure_artifacts'))
    
    def test_smart_error_analyzer_element_not_found(self):
        """Test SmartErrorAnalyzer for element not found"""
        mock_pilot = Mock()
        mock_pilot.current_url = "https://example.com"
        mock_pilot.is_page_loaded = Mock(return_value=True)
        
        analyzer = SmartErrorAnalyzer()
        analysis = analyzer.analyze_element_not_found("#test-button", mock_pilot)
        
        self.assertEqual(analysis["selector"], "#test-button")
        self.assertIn("suggestions", analysis)
        self.assertIn("possible_issues", analysis)
        self.assertEqual(analysis["current_url"], "https://example.com")
    
    def test_smart_error_analyzer_fix_suggestions(self):
        """Test SmartErrorAnalyzer generates fix suggestions"""
        analyzer = SmartErrorAnalyzer()
        mock_pilot = Mock()
        
        # Test element not found suggestion
        error = Exception("element not found")
        suggestion = analyzer.generate_fix_suggestion(error, mock_pilot)
        self.assertIn("Wait for element", suggestion)
        self.assertIn("iframe", suggestion)
        
        # Test timeout suggestion
        error = Exception("timeout waiting")
        suggestion = analyzer.generate_fix_suggestion(error, mock_pilot)
        self.assertIn("Increase timeout", suggestion)


class TestSmartErrors(unittest.TestCase):
    """Test smart error messages"""
    
    def test_smart_element_not_found_error(self):
        """Test SmartElementNotFoundError"""
        error = SmartElementNotFoundError(
            selector="#missing-button",
            similar_elements=["#missing-btn", "#missed-button"],
            suggestions=["Check spelling", "Wait for load"],
            page_info={"url": "https://example.com", "title": "Test Page"}
        )
        
        error_message = str(error)
        self.assertIn("#missing-button", error_message)
        self.assertIn("Did you mean", error_message)
        self.assertIn("#missing-btn", error_message)
        self.assertIn("Check spelling", error_message)
        self.assertIn("https://example.com", error_message)
    
    def test_smart_timeout_error(self):
        """Test SmartTimeoutError"""
        error = SmartTimeoutError(
            operation="waiting for element",
            timeout=10.0,
            element="#slow-element",
            suggestions=["Increase timeout", "Check network"]
        )
        
        error_message = str(error)
        self.assertIn("10s", error_message)
        self.assertIn("#slow-element", error_message)
        self.assertIn("Increase timeout", error_message)
    
    def test_smart_network_error(self):
        """Test SmartNetworkError"""
        error = SmartNetworkError(
            url="https://api.example.com/users",
            status_code=404,
            error_type="Not Found"
        )
        
        error_message = str(error)
        self.assertIn("https://api.example.com/users", error_message)
        self.assertIn("404", error_message)
        self.assertIn("Not Found", error_message)
        self.assertIn("doesn't exist", error_message)  # Status meaning
    
    def test_error_suggestion_engine_selector_alternatives(self):
        """Test ErrorSuggestionEngine suggests selector alternatives"""
        engine = ErrorSuggestionEngine()
        
        available = [
            "#submit-button",
            "#submit-btn",
            ".submit-form",
            "button.submit"
        ]
        
        suggestions = engine.suggest_selector_alternatives(
            "#submit-buton",  # Typo
            available
        )
        
        self.assertIn("#submit-button", suggestions)
        self.assertIn("#submit-btn", suggestions)
    
    def test_error_suggestion_engine_analyze_page_state(self):
        """Test ErrorSuggestionEngine analyzes page state"""
        engine = ErrorSuggestionEngine()
        
        mock_pilot = Mock()
        mock_pilot.current_url = "https://example.com"
        mock_pilot.title = "Test Page"
        mock_pilot.is_page_loaded = Mock(return_value=True)
        
        state = engine.analyze_page_state(mock_pilot)
        
        self.assertEqual(state["url"], "https://example.com")
        self.assertEqual(state["title"], "Test Page")
        self.assertEqual(state["is_loaded"], True)


class TestNetworkMocking(unittest.TestCase):
    """Test network mocking utilities"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mocker = NetworkMocker()
    
    def test_mock_response_exact_match(self):
        """Test exact URL matching"""
        self.mocker.mock_response(
            "https://api.example.com/users",
            json={"users": []},
            status=200
        )
        
        request = {"url": "https://api.example.com/users", "method": "GET"}
        response = self.mocker.handle_request(request)
        
        self.assertIsNotNone(response)
        self.assertEqual(response["status"], 200)
        self.assertIn("users", response["body"])
    
    def test_mock_response_regex_match(self):
        """Test regex URL matching"""
        self.mocker.mock_regex(
            r"https://api\.example\.com/users/\d+",
            json={"id": 1, "name": "Test"},
            status=200
        )
        
        request = {"url": "https://api.example.com/users/123", "method": "GET"}
        response = self.mocker.handle_request(request)
        
        self.assertIsNotNone(response)
        self.assertEqual(response["status"], 200)
    
    def test_mock_domain_match(self):
        """Test domain matching"""
        self.mocker.mock_domain(
            "api.example.com",
            json={"message": "Domain mock"},
            status=200
        )
        
        request = {"url": "https://api.example.com/any/path", "method": "GET"}
        response = self.mocker.handle_request(request)
        
        self.assertIsNotNone(response)
        self.assertEqual(response["status"], 200)
    
    def test_mock_error_response(self):
        """Test mocking error responses"""
        self.mocker.mock_error(
            "https://api.example.com/broken",
            status=500,
            error_message="Internal Server Error"
        )
        
        request = {"url": "https://api.example.com/broken", "method": "GET"}
        response = self.mocker.handle_request(request)
        
        self.assertIsNotNone(response)
        self.assertEqual(response["status"], 500)
        self.assertIn("error", response)
    
    def test_mock_with_method_matching(self):
        """Test method-specific mocking"""
        self.mocker.mock_response(
            "https://api.example.com/users",
            json={"created": True},
            status=201,
            method="POST"
        )
        
        # GET request should not match
        get_request = {"url": "https://api.example.com/users", "method": "GET"}
        get_response = self.mocker.handle_request(get_request)
        self.assertIsNone(get_response)
        
        # POST request should match
        post_request = {"url": "https://api.example.com/users", "method": "POST"}
        post_response = self.mocker.handle_request(post_request)
        self.assertIsNotNone(post_response)
        self.assertEqual(post_response["status"], 201)
    
    def test_mock_with_times_limit(self):
        """Test mocking with limited number of times"""
        self.mocker.mock_response(
            "https://api.example.com/limited",
            json={"data": "test"},
            status=200,
            times=2
        )
        
        request = {"url": "https://api.example.com/limited", "method": "GET"}
        
        # First two requests should be mocked
        response1 = self.mocker.handle_request(request)
        self.assertIsNotNone(response1)
        
        response2 = self.mocker.handle_request(request)
        self.assertIsNotNone(response2)
        
        # Third request should not be mocked
        response3 = self.mocker.handle_request(request)
        self.assertIsNone(response3)
    
    def test_request_counting(self):
        """Test request counting"""
        self.mocker.mock_response("https://api.example.com/count", json={})
        
        request = {"url": "https://api.example.com/count", "method": "GET"}
        
        self.mocker.handle_request(request)
        self.mocker.handle_request(request)
        
        count = self.mocker.get_request_count("https://api.example.com/count")
        self.assertEqual(count, 2)
    
    def test_assert_requested(self):
        """Test request assertions"""
        self.mocker.mock_response("https://api.example.com/test", json={})
        
        request = {"url": "https://api.example.com/test", "method": "GET"}
        self.mocker.handle_request(request)
        
        # Should not raise
        self.mocker.assert_requested("https://api.example.com/test")
        self.mocker.assert_requested("https://api.example.com/test", times=1)
        
        # Should raise
        with self.assertRaises(AssertionError):
            self.mocker.assert_requested("https://api.example.com/test", times=2)
    
    def test_unmatched_requests_tracking(self):
        """Test tracking of unmatched requests"""
        request = {"url": "https://unmocked.com/api", "method": "GET"}
        response = self.mocker.handle_request(request)
        
        self.assertIsNone(response)
        
        unmatched = self.mocker.get_unmatched_requests()
        self.assertEqual(len(unmatched), 1)
        self.assertEqual(unmatched[0]["url"], "https://unmocked.com/api")
    
    def test_mock_api_endpoints_helper(self):
        """Test mock_api_endpoints helper function"""
        mock_api_endpoints(self.mocker, "https://api.example.com", {
            "/users": {"users": []},
            "/posts": {"posts": []},
            "/auth/login": {"token": "abc123"}
        })
        
        # Test each endpoint
        users_req = {"url": "https://api.example.com/users", "method": "GET"}
        users_resp = self.mocker.handle_request(users_req)
        self.assertIsNotNone(users_resp)
        
        posts_req = {"url": "https://api.example.com/posts", "method": "GET"}
        posts_resp = self.mocker.handle_request(posts_req)
        self.assertIsNotNone(posts_resp)
        
        auth_req = {"url": "https://api.example.com/auth/login", "method": "GET"}
        auth_resp = self.mocker.handle_request(auth_req)
        self.assertIsNotNone(auth_resp)


class TestIntegration(unittest.TestCase):
    """Integration tests for v1.4.1 features working together"""
    
    def test_retry_with_smart_errors(self):
        """Test retry mechanism with smart error messages"""
        call_count = 0
        
        @retry(times=2, delay=0.1, exceptions=(SmartElementNotFoundError,))
        def click_with_smart_error():
            nonlocal call_count
            call_count += 1
            raise SmartElementNotFoundError(
                selector="#button",
                suggestions=["Wait for element", "Check iframe"]
            )
        
        with self.assertRaises(SmartElementNotFoundError) as cm:
            click_with_smart_error()
        
        self.assertEqual(call_count, 2)
        error_message = str(cm.exception)
        self.assertIn("#button", error_message)
        self.assertIn("Wait for element", error_message)
    
    def test_failure_capture_with_network_mock(self):
        """Test failure capture with network mocking"""
        temp_dir = tempfile.mkdtemp()
        failure_capture = FailureCapture(directory=temp_dir)
        mocker = NetworkMocker()
        
        # Mock network responses
        mocker.mock_response("https://api.example.com/data", json={"test": "data"})
        
        # Mock pilot with network mocker
        mock_pilot = Mock()
        mock_pilot.network_mocker = mocker
        mock_pilot.screenshot = Mock()
        mock_pilot.get_network_logs = Mock(return_value=mocker.request_log)
        
        @capture_on_failure(failure_capture)
        def test_with_mocking(pilot):
            # Simulate network request
            request = {"url": "https://api.example.com/data", "method": "GET"}
            pilot.network_mocker.handle_request(request)
            raise ValueError("Test error")
        
        with self.assertRaises(ValueError) as cm:
            test_with_mocking(mock_pilot)
        
        # Check that network logs were captured
        self.assertTrue(hasattr(cm.exception, 'failure_artifacts'))


def run_tests():
    """Run all v1.4.1 feature tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestRetryMechanisms))
    suite.addTests(loader.loadTestsFromTestCase(TestFailureCapture))
    suite.addTests(loader.loadTestsFromTestCase(TestSmartErrors))
    suite.addTests(loader.loadTestsFromTestCase(TestNetworkMocking))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)