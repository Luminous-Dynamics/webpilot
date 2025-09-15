#!/usr/bin/env python3
"""
WebPilot v1.4.1 Features Demo

Demonstrates the new features added in v1.4.1:
- Retry mechanism for flaky tests
- Automatic failure capture with screenshots
- Smart error messages with suggestions
- Network mocking for faster tests
"""

from webpilot import WebPilot, BrowserType
from webpilot.utils.retry import retry, RetryableOperation
from webpilot.utils.failure_capture import FailureCapture, capture_on_failure
from webpilot.utils.smart_errors import SmartElementNotFoundError, SmartTimeoutError
from webpilot.utils.network_mock import NetworkMocker, mock_api_endpoints


def demo_retry_mechanism():
    """Demo 1: Automatic retry for flaky operations"""
    print("\n" + "="*60)
    print("DEMO 1: Retry Mechanism")
    print("="*60)
    
    pilot = WebPilot(
        browser=BrowserType.FIREFOX,
        retry_config={'times': 3, 'delay': 1, 'backoff': 2}
    )
    
    # Start browser
    pilot.start("https://example.com")
    
    # Click with automatic retry on failure
    result = pilot.click(x=100, y=200, retry_on_fail=True)
    print(f"Click result (with retry): {result.success}")
    
    # Using retry decorator
    @retry(times=3, delay=0.5)
    def flaky_operation():
        # This might fail sometimes
        return pilot.click(selector="#dynamic-button")
    
    try:
        flaky_operation()
        print("Flaky operation succeeded after retries")
    except Exception as e:
        print(f"Failed even after retries: {e}")
    
    # Using RetryableOperation context manager
    with RetryableOperation(times=5) as retry_op:
        while retry_op.should_retry():
            try:
                pilot.wait_for_element("#slow-loading-element", timeout=2)
                retry_op.success()
                print("Element found!")
            except:
                retry_op.failed()
                print(f"Attempt {retry_op.attempt} failed, retrying...")
    
    pilot.close()


def demo_failure_capture():
    """Demo 2: Automatic failure capture with diagnostics"""
    print("\n" + "="*60)
    print("DEMO 2: Failure Capture")
    print("="*60)
    
    # Configure failure capture
    failure_capture = FailureCapture(
        screenshot=True,
        html=True,
        console_logs=True,
        network_logs=True,
        performance_metrics=True,
        directory="./test-failures"
    )
    
    pilot = WebPilot(
        browser=BrowserType.FIREFOX,
        failure_capture=failure_capture
    )
    
    # Using decorator for automatic capture
    @capture_on_failure(failure_capture)
    def test_login_flow(pilot):
        pilot.start("https://example.com/login")
        pilot.type_text("test@example.com")
        pilot.press_key("Tab")
        pilot.type_text("password123")
        # This might fail and will capture diagnostics
        pilot.click(selector="#non-existent-button")
    
    try:
        test_login_flow(pilot)
    except Exception as e:
        print(f"Test failed, but diagnostics captured!")
        if hasattr(e, 'failure_artifacts'):
            print(f"Artifacts saved to: {e.failure_artifacts['directory']}")
            print(f"Screenshot: {e.failure_artifacts.get('screenshot')}")
            print(f"HTML: {e.failure_artifacts.get('html')}")
            print(f"Console logs: {e.failure_artifacts.get('console_logs')}")
    
    pilot.close()


def demo_smart_errors():
    """Demo 3: Smart error messages with helpful suggestions"""
    print("\n" + "="*60)
    print("DEMO 3: Smart Error Messages")
    print("="*60)
    
    pilot = WebPilot(browser=BrowserType.FIREFOX)
    pilot.start("https://example.com")
    
    # Smart element not found error
    try:
        pilot.click(selector="#misspelled-buttn")  # Typo in selector
    except SmartElementNotFoundError as e:
        print("Smart error caught!")
        print(e)  # Will show suggestions and similar elements
    
    # Smart timeout error
    try:
        pilot.wait_for_element("#slow-element", timeout=1)
    except SmartTimeoutError as e:
        print("\nSmart timeout error:")
        print(e)  # Will show timeout context and suggestions
    
    pilot.close()


def demo_network_mocking():
    """Demo 4: Network mocking for faster tests"""
    print("\n" + "="*60)
    print("DEMO 4: Network Mocking")
    print("="*60)
    
    # Create network mocker
    mocker = NetworkMocker()
    
    # Mock API responses
    mocker.mock_response(
        "https://api.example.com/users",
        json={"users": [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ]},
        status=200
    )
    
    # Mock with regex pattern
    mocker.mock_regex(
        r"https://api\.example\.com/users/\d+",
        json={"id": 1, "name": "Test User", "email": "test@example.com"}
    )
    
    # Mock slow endpoints to be fast
    mocker.mock_response(
        "https://slow-api.com/search",
        json={"results": []},
        delay=0.1  # Instead of 5 seconds
    )
    
    # Mock errors for testing error handling
    mocker.mock_error(
        "https://api.example.com/broken",
        status=500,
        error_message="Internal Server Error"
    )
    
    # Create pilot with mocker
    pilot = WebPilot(
        browser=BrowserType.FIREFOX,
        network_mocker=mocker
    )
    
    pilot.start("https://example.com")
    
    # The mocked responses will be used instead of real network calls
    # This makes tests much faster and more reliable
    
    # Check request counts
    print(f"API called {mocker.get_request_count('api.example.com')} times")
    
    # Assert specific requests were made
    try:
        mocker.assert_requested("https://api.example.com/users", times=1)
        print("API endpoint was called exactly once")
    except AssertionError as e:
        print(f"Assertion failed: {e}")
    
    # Check unmatched requests (useful for finding missing mocks)
    unmatched = mocker.get_unmatched_requests()
    if unmatched:
        print(f"Unmatched requests: {unmatched}")
    
    pilot.close()


def demo_combined_features():
    """Demo 5: Using all features together"""
    print("\n" + "="*60)
    print("DEMO 5: Combined Features")
    print("="*60)
    
    # Setup comprehensive configuration
    failure_capture = FailureCapture(
        screenshot=True,
        html=True,
        directory="./combined-test-failures"
    )
    
    mocker = NetworkMocker()
    mock_api_endpoints(mocker, "https://api.example.com", {
        "/auth/login": {"token": "abc123", "success": True},
        "/users/profile": {"name": "Test User", "email": "test@example.com"},
        "/dashboard/data": {"widgets": [], "notifications": 0}
    })
    
    pilot = WebPilot(
        browser=BrowserType.FIREFOX,
        failure_capture=failure_capture,
        network_mocker=mocker,
        retry_config={'times': 3, 'delay': 0.5}
    )
    
    @capture_on_failure(failure_capture)
    @retry(times=3, delay=1)
    def test_user_flow():
        # Start and navigate
        pilot.start("https://example.com")
        
        # Wait for page load with network idle
        pilot.wait_for_network_idle()
        
        # Login with retry on element clicks
        pilot.click(selector="#login-button", retry_on_fail=True)
        pilot.type_text("test@example.com")
        pilot.press_key("Tab")
        pilot.type_text("password123")
        pilot.click(selector="#submit", retry_on_fail=True)
        
        # Wait for dashboard
        pilot.wait_for_element("#dashboard", timeout=10)
        
        # Take screenshot for verification
        pilot.screenshot("dashboard.png")
        
        # Get session report
        report = pilot.get_session_report()
        print(f"Session report: {report}")
    
    try:
        test_user_flow()
        print("✅ Test passed with all features working!")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        if hasattr(e, 'failure_artifacts'):
            print(f"Check diagnostics at: {e.failure_artifacts['directory']}")
    finally:
        pilot.close()


def main():
    """Run all demos"""
    print("WebPilot v1.4.1 Features Demo")
    print("=============================")
    
    demos = [
        ("Retry Mechanism", demo_retry_mechanism),
        ("Failure Capture", demo_failure_capture),
        ("Smart Errors", demo_smart_errors),
        ("Network Mocking", demo_network_mocking),
        ("Combined Features", demo_combined_features)
    ]
    
    for name, demo_func in demos:
        try:
            demo_func()
        except Exception as e:
            print(f"\n⚠️ Demo '{name}' encountered an error: {e}")
            print("This is expected for demonstration purposes!")
    
    print("\n" + "="*60)
    print("All demos completed!")
    print("="*60)


if __name__ == "__main__":
    main()