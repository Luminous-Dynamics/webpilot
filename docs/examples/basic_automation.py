#!/usr/bin/env python3
"""
Basic WebPilot Automation Example
Demonstrates core functionality
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from webpilot import WebPilot, BrowserType


def main():
    """Basic automation example"""
    
    print("🚁 WebPilot Basic Automation Example")
    print("=" * 50)
    
    # Create WebPilot instance
    pilot = WebPilot(browser=BrowserType.FIREFOX)
    
    try:
        # 1. Start browser and navigate
        print("\n1. Starting browser...")
        result = pilot.start("https://example.com")
        if result.success:
            print(f"   ✅ Browser started (PID: {result.data['pid']})")
        else:
            print(f"   ❌ Failed: {result.error}")
            return
            
        # 2. Wait for page load
        print("\n2. Waiting for page load...")
        pilot.wait(2)
        print("   ✅ Page loaded")
        
        # 3. Take screenshot
        print("\n3. Taking screenshot...")
        result = pilot.screenshot("example_page.png")
        if result.success:
            print(f"   ✅ Screenshot saved: {result.data['path']}")
            print(f"   Size: {result.data['size']} bytes")
        
        # 4. Scroll down
        print("\n4. Scrolling down...")
        result = pilot.scroll("down", amount=3)
        if result.success:
            print("   ✅ Scrolled down")
            
        # 5. Navigate to another page
        print("\n5. Navigating to Python.org...")
        result = pilot.navigate("https://python.org")
        if result.success:
            print("   ✅ Navigated successfully")
            
        pilot.wait(2)
        
        # 6. Take another screenshot
        print("\n6. Taking screenshot of Python.org...")
        result = pilot.screenshot("python_page.png")
        if result.success:
            print(f"   ✅ Screenshot saved: {result.data['path']}")
            
        # 7. Extract page content
        print("\n7. Extracting page content...")
        result = pilot.extract_page_content()
        if result.success:
            print(f"   ✅ Extracted {result.data['length']} bytes")
            print(f"   Preview: {result.data['content_preview'][:100]}...")
            
        # 8. Get session report
        print("\n8. Session Report:")
        report = pilot.get_session_report()
        print(f"   Session ID: {report['session_id']}")
        print(f"   Total actions: {report['total_actions']}")
        print(f"   Screenshots taken: {report['screenshots_taken']}")
        print(f"   Session directory: {report['session_dir']}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        
    finally:
        # Close browser
        print("\n9. Closing browser...")
        pilot.close()
        print("   ✅ Browser closed")
        
    print("\n✨ Automation complete!")


if __name__ == "__main__":
    main()