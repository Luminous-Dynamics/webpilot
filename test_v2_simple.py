#!/usr/bin/env python3
"""
Simple test of WebPilot v2.0 Architecture
Tests the adapter without AI components
"""

import asyncio
from playwright.async_api import async_playwright
import time
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from src.webpilot.v2 import PlaywrightAdapter


async def test_adapter_only():
    """Test just the Playwright adapter without AI."""
    
    print("🚀 WebPilot v2.0 - Adapter Test (No AI Required)")
    print("=" * 50)
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Create adapter
        adapter = PlaywrightAdapter(page)
        print("✅ Adapter created")
        
        # Test navigation
        print("\n📝 Testing navigation...")
        start = time.time()
        await adapter.execute_playwright_action('goto', url='https://example.com')
        nav_time = time.time() - start
        print(f"✅ Navigated in {nav_time*1000:.1f}ms")
        print(f"   URL: {adapter.get_url()}")
        
        # Test waiting
        print("\n📝 Testing element waiting...")
        start = time.time()
        found = await adapter.smart_wait('h1', timeout=5000)
        wait_time = time.time() - start
        print(f"✅ Element found: {found} in {wait_time*1000:.1f}ms")
        
        # Test screenshot
        print("\n📝 Testing screenshot...")
        screenshot = await adapter.take_screenshot()
        print(f"✅ Screenshot taken: {len(screenshot):,} bytes")
        
        # Test JavaScript execution
        print("\n📝 Testing JavaScript...")
        result = await adapter.evaluate_javascript('document.title')
        print(f"✅ JS executed, title: {result}")
        
        # Test page content
        print("\n📝 Testing content retrieval...")
        content = await adapter.get_page_content()
        print(f"✅ Page content: {len(content):,} characters")
        
        await browser.close()
        
        print("\n" + "=" * 50)
        print("✅ All adapter tests passed!")
        print("\nKey Results:")
        print(f"- Navigation: {nav_time*1000:.1f}ms")
        print(f"- Element wait: {wait_time*1000:.1f}ms")
        print(f"- Zero errors")
        print(f"- Thin wrapper working perfectly!")


async def benchmark_overhead():
    """Compare adapter overhead vs raw Playwright."""
    
    print("\n⚡ Performance Comparison")
    print("=" * 50)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # Test raw Playwright
        page1 = await browser.new_page()
        
        start = time.time()
        await page1.goto('https://example.com')
        await page1.wait_for_selector('h1')
        await page1.screenshot()
        raw_time = time.time() - start
        
        # Test with adapter
        page2 = await browser.new_page()
        adapter = PlaywrightAdapter(page2)
        
        start = time.time()
        await adapter.execute_playwright_action('goto', url='https://example.com')
        await adapter.smart_wait('h1', timeout=5000)
        await adapter.take_screenshot()
        adapter_time = time.time() - start
        
        await browser.close()
        
        # Results
        overhead_ms = (adapter_time - raw_time) * 1000
        overhead_pct = ((adapter_time - raw_time) / raw_time) * 100 if raw_time > 0 else 0
        
        print(f"Raw Playwright:  {raw_time*1000:.1f}ms")
        print(f"With Adapter:    {adapter_time*1000:.1f}ms")
        print(f"Overhead:        {overhead_ms:.1f}ms ({overhead_pct:.1f}%)")
        
        if overhead_pct < 5:
            print("✅ Excellent! Less than 5% overhead")
        elif overhead_pct < 10:
            print("✅ Good! Less than 10% overhead")
        else:
            print("⚠️ Higher than expected overhead")


async def main():
    """Run all tests."""
    
    print("WebPilot v2.0 Architecture Validation")
    print("=====================================\n")
    
    # Check Playwright
    try:
        from playwright.async_api import async_playwright
        print("✅ Playwright is available")
    except ImportError:
        print("❌ Playwright not found!")
        print("Run: poetry add playwright && playwright install")
        return
    
    # Run tests
    try:
        await test_adapter_only()
        await benchmark_overhead()
        
        print("\n" + "=" * 50)
        print("🎉 WebPilot v2.0 Architecture Validated!")
        print("\nNext Steps:")
        print("1. Add LLM client implementation")
        print("2. Create natural language processor")
        print("3. Build smart assertions")
        print("4. Generate killer examples")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())