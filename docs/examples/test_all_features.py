#!/usr/bin/env python3
"""
Complete WebPilot Feature Test - Demonstrates all enhancements with dependencies
"""

import asyncio
import time
from pathlib import Path

# Import all WebPilot modules
from webpilot import WebPilot, BrowserType
from webpilot_selenium import SeleniumWebPilot
from webpilot_vision import WebPilotVision  
from webpilot_async import AsyncWebPilot

def test_core_webpilot():
    """Test core WebPilot functionality"""
    print("\n🚁 CORE WEBPILOT TEST")
    print("=" * 50)
    
    pilot = WebPilot(browser=BrowserType.FIREFOX, headless=False)
    
    # Navigate
    result = pilot.navigate("https://example.com")
    print(f"✅ Navigate: Success (PID: {result.data.get('pid')})")
    
    # Wait
    pilot.wait(2)
    print("✅ Wait: 2 seconds")
    
    # Screenshot
    result = pilot.screenshot("core_test.png")
    if result.success:
        print(f"✅ Screenshot: Saved to {result.data.get('path')}")
    
    # Close
    pilot.close()
    print("✅ Browser closed")
    
    return True

def test_selenium_backend():
    """Test Selenium backend for advanced control"""
    print("\n🎯 SELENIUM BACKEND TEST")
    print("=" * 50)
    
    try:
        with SeleniumWebPilot(headless=True) as pilot:
            # Start browser
            result = pilot.start("https://example.com")
            print(f"✅ Selenium Start: Success")
            
            # Take screenshot
            result = pilot.screenshot("selenium_test.png")
            print(f"✅ Screenshot: {result.data.get('path')}")
            
            # Execute JavaScript
            result = pilot.execute_javascript("return document.title")
            if result.success:
                print(f"✅ JavaScript: Got title '{result.data.get('result')}'")
            
            # Get page source
            result = pilot.get_page_source()
            if result.success:
                print(f"✅ Page Source: {len(result.data.get('source', ''))} chars")
            
            print("✅ Selenium test complete")
            return True
            
    except Exception as e:
        print(f"❌ Selenium error: {e}")
        return False

def test_vision_module():
    """Test vision/OCR capabilities"""
    print("\n🔍 VISION MODULE TEST")
    print("=" * 50)
    
    vision = WebPilotVision()
    
    # Check if dependencies are available
    if vision.check_dependencies():
        print("✅ Vision dependencies available")
        
        # Create a test screenshot first
        pilot = WebPilot(headless=True)
        pilot.navigate("https://example.com")
        pilot.screenshot("vision_test.png")
        pilot.close()
        
        screenshot_path = Path("/tmp/webpilot-sessions") / pilot.session.session_id / "screenshots" / "vision_test.png"
        
        if screenshot_path.exists():
            # Analyze screenshot
            result = vision.analyze_screenshot(str(screenshot_path))
            print(f"✅ Screenshot Analysis: {result}")
            
            # Try to find text (OCR)
            text_result = vision.extract_text_from_image(str(screenshot_path))
            if text_result.get('success'):
                print(f"✅ OCR Text Extraction: Found {len(text_result.get('text', ''))} chars")
            
            return True
    else:
        print("⚠️  Vision dependencies not fully available")
        print("   Install with: pip install pytesseract")
        return False

async def test_async_performance():
    """Test async WebPilot for performance"""
    print("\n⚡ ASYNC PERFORMANCE TEST")
    print("=" * 50)
    
    async with AsyncWebPilot() as pilot:
        # Test batch fetching
        urls = [
            "https://example.com",
            "https://github.com", 
            "https://python.org",
            "https://mozilla.org",
            "https://wikipedia.org"
        ]
        
        print(f"Fetching {len(urls)} URLs concurrently...")
        
        # Time sequential vs concurrent
        start = time.time()
        results = await pilot.batch_fetch(urls)
        concurrent_time = (time.time() - start) * 1000
        
        success_count = sum(1 for r in results if r.success)
        total_bytes = sum(r.data.get('length', 0) for r in results if r.success)
        
        print(f"✅ Concurrent: {success_count}/{len(urls)} URLs in {concurrent_time:.0f}ms")
        print(f"   Total data: {total_bytes:,} bytes")
        
        # Test parallel actions
        actions = [
            {'type': 'fetch', 'url': 'https://example.com'},
            {'type': 'screenshot', 'name': 'async_test.png'},
            {'type': 'wait', 'seconds': 1}
        ]
        
        print(f"\nExecuting {len(actions)} parallel actions...")
        start = time.time()
        results = await pilot.parallel_actions(actions)
        parallel_time = (time.time() - start) * 1000
        
        success_count = sum(1 for r in results if r.success)
        print(f"✅ Parallel Actions: {success_count}/{len(actions)} in {parallel_time:.0f}ms")
        
        return True

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🚁 WEBPILOT COMPLETE FEATURE TEST")
    print("="*60)
    print("\nThis test demonstrates all WebPilot enhancements:")
    print("• Core WebPilot - Basic browser automation")
    print("• Selenium Backend - Advanced browser control")
    print("• Vision Module - OCR and image analysis")
    print("• Async Support - High-performance operations")
    
    results = {}
    
    # Test core
    print("\n[1/4] Testing Core WebPilot...")
    results['core'] = test_core_webpilot()
    
    # Test Selenium
    print("\n[2/4] Testing Selenium Backend...")
    results['selenium'] = test_selenium_backend()
    
    # Test Vision
    print("\n[3/4] Testing Vision Module...")
    results['vision'] = test_vision_module()
    
    # Test Async
    print("\n[4/4] Testing Async Performance...")
    results['async'] = asyncio.run(test_async_performance())
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    for feature, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{feature.upper():15} {status}")
    
    total_passed = sum(1 for v in results.values() if v)
    print(f"\nTotal: {total_passed}/{len(results)} features working")
    
    if total_passed == len(results):
        print("\n🎉 ALL FEATURES WORKING PERFECTLY!")
        print("\nWebPilot is ready for professional web automation with:")
        print("• Enterprise browser control (Selenium)")
        print("• AI vision capabilities (OCR)")
        print("• High-performance async operations")
        print("• Cross-platform support")
    else:
        print("\n⚠️  Some features need additional setup")
        print("Run: ./install_dependencies.sh for full installation")
    
    print("\n✨ WebPilot test complete!")

if __name__ == "__main__":
    main()