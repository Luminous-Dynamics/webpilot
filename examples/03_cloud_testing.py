#!/usr/bin/env python3
"""
WebPilot Cloud Testing Example

This example demonstrates:
- Setting up cloud browser providers
- Running tests across multiple browsers/OS
- Matrix testing strategies
- Collecting cloud test results
"""

import os
import sys
from pathlib import Path
from typing import Dict, List

# Add parent directory to path for local testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from webpilot.cloud import (
    CloudWebPilot,
    CloudConfig,
    CloudProvider,
    CloudTestRunner
)


def setup_browserstack():
    """Set up BrowserStack configuration."""
    # Get credentials from environment variables
    username = os.environ.get("BROWSERSTACK_USERNAME", "your_username")
    access_key = os.environ.get("BROWSERSTACK_ACCESS_KEY", "your_key")
    
    if username == "your_username":
        print("⚠️  Please set BROWSERSTACK_USERNAME and BROWSERSTACK_ACCESS_KEY")
        print("   Get your credentials from: https://www.browserstack.com/accounts/settings")
        return None
    
    config = CloudConfig(
        provider=CloudProvider.BROWSERSTACK,
        username=username,
        access_key=access_key,
        project_name="WebPilot Demo",
        build_name="Cloud Testing Example",
        video_recording=True,
        network_logs=True,
        console_logs=True
    )
    
    return config


def setup_sauce_labs():
    """Set up Sauce Labs configuration."""
    username = os.environ.get("SAUCE_USERNAME")
    access_key = os.environ.get("SAUCE_ACCESS_KEY")
    
    if not username or not access_key:
        return None
    
    config = CloudConfig(
        provider=CloudProvider.SAUCE_LABS,
        username=username,
        access_key=access_key,
        project_name="WebPilot Demo",
        build_name="Cloud Testing Example",
        video_recording=True
    )
    
    return config


def run_single_cloud_test(config: CloudConfig):
    """Run a single test on cloud browser."""
    print("\n☁️  Running Single Cloud Test")
    print("=" * 50)
    
    with CloudWebPilot(
        config,
        browser="chrome",
        browser_version="latest",
        os_name="Windows",
        os_version="11"
    ) as pilot:
        # Navigate to test site
        print(f"\n🌐 Starting {config.provider.value} browser...")
        result = pilot.start("https://www.example.com")
        
        if result.success:
            print(f"✅ Browser started: {result.data.get('browser')} on {result.data.get('os')}")
            print(f"📺 Session URL: {pilot.get_session_url()}")
        else:
            print(f"❌ Failed to start: {result.error}")
            return
        
        # Take screenshot
        print("\n📸 Taking screenshot...")
        screenshot = pilot.screenshot("cloud_screenshot.png")
        if screenshot.success:
            print("✅ Screenshot captured")
        
        # Perform some actions
        print("\n🎯 Performing test actions...")
        
        # Check page title
        title = pilot.driver.title
        print(f"  Page title: {title}")
        
        # Find elements
        elements = pilot.find_elements("a")
        print(f"  Found {len(elements)} links")
        
        # Test network throttling (BrowserStack only)
        if config.provider == CloudProvider.BROWSERSTACK:
            print("\n🐌 Testing network throttling...")
            throttle_result = pilot.enable_network_throttling("Regular3G")
            if throttle_result.success:
                print("✅ Network throttled to 3G")
        
        # Get logs
        print("\n📋 Collecting logs...")
        
        # Network logs
        network_logs = pilot.get_network_logs()
        if network_logs:
            print(f"  Network logs: {len(network_logs)} entries")
        
        # Console logs
        console_logs = pilot.get_console_logs()
        if console_logs:
            print(f"  Console logs: {len(console_logs)} entries")
        
        # Mark test status
        pilot.mark_test_status(
            passed=True,
            reason="Test completed successfully"
        )
        print("\n✅ Test marked as passed")


def run_matrix_testing(config: CloudConfig):
    """Run tests across multiple browser/OS combinations."""
    print("\n🎯 Running Matrix Testing")
    print("=" * 50)
    
    # Define test function
    def test_function(pilot):
        """Test function to run on each configuration."""
        # Navigate to site
        pilot.start("https://www.example.com")
        
        # Perform test actions
        title = pilot.driver.title
        elements = pilot.find_elements("a")
        
        # Take screenshot
        pilot.screenshot("matrix_test.png")
        
        # Return test result
        return {
            "passed": True,
            "title": title,
            "link_count": len(elements),
            "reason": "Test completed successfully"
        }
    
    # Create test runner
    runner = CloudTestRunner(config)
    
    # Define test matrix
    configurations = [
        {"browser": "chrome", "browser_version": "latest", "os": "Windows", "os_version": "11"},
        {"browser": "firefox", "browser_version": "latest", "os": "Windows", "os_version": "10"},
        {"browser": "safari", "browser_version": "latest", "os": "OS X", "os_version": "Monterey"},
        {"browser": "edge", "browser_version": "latest", "os": "Windows", "os_version": "11"},
    ]
    
    print(f"\n📊 Testing on {len(configurations)} configurations...")
    
    # Run tests
    results = runner.run_on_matrix(test_function, configurations)
    
    # Display results
    print("\n📈 Test Results:")
    print("-" * 50)
    
    for result in results:
        config_str = f"{result['config']['browser']} on {result['config']['os']} {result['config']['os_version']}"
        
        if 'error' in result:
            print(f"❌ {config_str}: {result['error']}")
        else:
            test_result = result['result']
            status = "✅" if test_result.get('passed') else "❌"
            print(f"{status} {config_str}: {test_result.get('reason')}")
            print(f"   - Title: {test_result.get('title')}")
            print(f"   - Links: {test_result.get('link_count')}")
            print(f"   - Session: {result.get('session_url')}")
    
    # Summary
    passed = sum(1 for r in results if 'result' in r and r['result'].get('passed'))
    failed = len(results) - passed
    
    print(f"\n📊 Summary: {passed} passed, {failed} failed")


def generate_test_matrix():
    """Generate comprehensive test matrix."""
    print("\n🔧 Generating Test Matrix")
    print("=" * 50)
    
    runner = CloudTestRunner(CloudConfig(
        provider=CloudProvider.BROWSERSTACK,
        username="dummy",
        access_key="dummy"
    ))
    
    # Generate default matrix
    matrix = runner.generate_matrix()
    
    print(f"Generated {len(matrix)} test configurations:")
    for config in matrix[:10]:  # Show first 10
        print(f"  - {config['browser']} on {config['os']} {config['os_version']}")
    
    if len(matrix) > 10:
        print(f"  ... and {len(matrix) - 10} more")
    
    # Custom matrix
    print("\n🎯 Custom Test Matrix:")
    custom_matrix = runner.generate_matrix(
        browsers=["chrome", "firefox"],
        operating_systems=[
            {"os": "Windows", "os_version": "11"},
            {"os": "OS X", "os_version": "Monterey"}
        ]
    )
    
    print(f"Generated {len(custom_matrix)} custom configurations:")
    for config in custom_matrix:
        print(f"  - {config['browser']} on {config['os']} {config['os_version']}")


def parallel_cloud_testing():
    """Demonstrate parallel testing across providers."""
    print("\n⚡ Parallel Cloud Testing")
    print("=" * 50)
    
    # This would run tests in parallel across multiple providers
    # For demonstration, we'll show the concept
    
    print("\nParallel testing workflow:")
    print("1. Initialize multiple cloud providers")
    print("2. Create thread pool or async tasks")
    print("3. Run same test on each provider")
    print("4. Collect and compare results")
    print("5. Generate unified report")
    
    print("\nExample code structure:")
    print("-" * 40)
    print("""
from concurrent.futures import ThreadPoolExecutor

def run_on_provider(provider_config):
    with CloudWebPilot(provider_config) as pilot:
        # Run test
        return test_result

configs = [browserstack_config, sauce_labs_config, lambdatest_config]

with ThreadPoolExecutor(max_workers=3) as executor:
    results = executor.map(run_on_provider, configs)
    """)


def main():
    """Run cloud testing examples."""
    print("☁️  WebPilot Cloud Testing Examples")
    print("=" * 50)
    
    # Try to set up BrowserStack
    config = setup_browserstack()
    
    if config:
        print("\n✅ BrowserStack configured")
        
        # Run single test
        run_single_cloud_test(config)
        
        # Run matrix testing
        run_matrix_testing(config)
    else:
        print("\n⚠️  No cloud provider configured")
        print("   Running demonstration mode...")
        
        # Show matrix generation
        generate_test_matrix()
        
        # Show parallel testing concept
        parallel_cloud_testing()
        
        print("\n💡 To run actual cloud tests:")
        print("   1. Sign up for BrowserStack: https://www.browserstack.com")
        print("   2. Get your credentials from account settings")
        print("   3. Export environment variables:")
        print("      export BROWSERSTACK_USERNAME=your_username")
        print("      export BROWSERSTACK_ACCESS_KEY=your_key")
        print("   4. Run this script again")
    
    print("\n✨ Cloud testing examples complete!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()