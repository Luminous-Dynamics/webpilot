#!/usr/bin/env python3
"""
WebPilot Basic Automation Example

This example demonstrates basic browser automation capabilities including:
- Navigation
- Element interaction
- Screenshots
- Form filling
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for local testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from webpilot import WebPilot, BrowserType


def main():
    """Run basic automation example."""
    print("🚁 WebPilot Basic Automation Example")
    print("=" * 50)
    
    # Initialize WebPilot with Chrome browser
    with WebPilot(browser=BrowserType.CHROME, headless=False) as pilot:
        # Navigate to example website
        print("\n1. Navigating to example.com...")
        result = pilot.start("https://example.com")
        
        if result.success:
            print(f"   ✅ Page loaded: {pilot.driver.title}")
        else:
            print(f"   ❌ Failed to load page: {result.error}")
            return
        
        # Take a screenshot
        print("\n2. Taking screenshot...")
        screenshot_result = pilot.screenshot("example_homepage.png")
        
        if screenshot_result.success:
            print(f"   ✅ Screenshot saved: {screenshot_result.data['path']}")
        else:
            print(f"   ❌ Screenshot failed: {screenshot_result.error}")
        
        # Navigate to a form page (using httpbin for testing)
        print("\n3. Navigating to form page...")
        pilot.navigate("https://httpbin.org/forms/post")
        
        # Fill out form fields
        print("\n4. Filling out form...")
        
        # Type in customer name
        pilot.type_text("John Doe", selector='input[name="custname"]')
        print("   ✅ Entered customer name")
        
        # Type in telephone
        pilot.type_text("555-1234", selector='input[name="custtel"]')
        print("   ✅ Entered telephone")
        
        # Type in email
        pilot.type_text("john@example.com", selector='input[name="custemail"]')
        print("   ✅ Entered email")
        
        # Select pizza size (using JavaScript)
        pilot.execute_script("""
            document.querySelector('input[value="medium"]').checked = true;
        """)
        print("   ✅ Selected pizza size")
        
        # Select toppings
        pilot.execute_script("""
            document.querySelector('input[value="bacon"]').checked = true;
            document.querySelector('input[value="cheese"]').checked = true;
        """)
        print("   ✅ Selected toppings")
        
        # Type delivery instructions
        pilot.type_text(
            "Please ring the doorbell twice",
            selector='textarea[name="comments"]'
        )
        print("   ✅ Added delivery instructions")
        
        # Take screenshot of filled form
        print("\n5. Taking screenshot of filled form...")
        pilot.screenshot("filled_form.png")
        print("   ✅ Form screenshot saved")
        
        # Submit form (commented out to avoid actual submission)
        # print("\n6. Submitting form...")
        # pilot.click(selector='button[type="submit"]')
        # print("   ✅ Form submitted")
        
        # Get page information
        print("\n7. Page Information:")
        print(f"   - Current URL: {pilot.driver.current_url}")
        print(f"   - Page Title: {pilot.driver.title}")
        print(f"   - Window Size: {pilot.driver.get_window_size()}")
        
        # Extract some data
        print("\n8. Extracting data...")
        elements = pilot.find_elements("input")
        print(f"   - Found {len(elements)} input elements")
        
        # Wait for user to see the results
        print("\n✨ Automation complete! Browser will close in 5 seconds...")
        import time
        time.sleep(5)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()