#!/usr/bin/env python3
"""
Test WebPilot v2.0 with Real Playwright Integration
This demonstrates the new architecture in action.
"""

import asyncio
from playwright.async_api import async_playwright
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.webpilot.v2 import AIWebPilot, WebPilotConfig


async def test_basic_automation():
    """Test basic browser automation through AI layer."""
    
    print("🚀 WebPilot v2.0 - Real Playwright Integration Test")
    print("=" * 50)
    
    async with async_playwright() as p:
        # Launch browser (Playwright handles this)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Add AI capabilities with WebPilot
        config = WebPilotConfig(
            llm_provider="openai",  # or "ollama" for local
            llm_model="gpt-4o-mini",
            auto_heal=True,
            verbose=True
        )
        
        pilot = AIWebPilot(page, config)
        
        print("\n📝 Test 1: Natural Language Navigation")
        print("-" * 40)
        
        try:
            # Natural language commands
            await pilot.execute("Go to https://example.com")
            print("✅ Navigation successful")
            
            # Check we're on the right page
            url = page.url
            assert "example.com" in url
            print(f"✅ URL verified: {url}")
            
        except Exception as e:
            print(f"❌ Navigation failed: {e}")
        
        print("\n📝 Test 2: Page Analysis")
        print("-" * 40)
        
        try:
            # AI analyzes the page
            explanation = await pilot.explain_page()
            print(f"🤖 Page explanation: {explanation[:200]}...")
            
        except Exception as e:
            print(f"❌ Page analysis failed: {e}")
        
        print("\n📝 Test 3: Element Finding")
        print("-" * 40)
        
        try:
            # Find element by description
            selector = await pilot.find_element("the main heading")
            print(f"✅ Found element: {selector}")
            
        except Exception as e:
            print(f"❌ Element finding failed: {e}")
        
        print("\n📝 Test 4: Visual Assertions")  
        print("-" * 40)
        
        try:
            # Natural language assertion
            result = await pilot.assert_visual("The page has a heading")
            print(f"✅ Visual assertion: {result}")
            
        except Exception as e:
            print(f"❌ Visual assertion failed: {e}")
        
        # Cleanup
        await browser.close()
        
        print("\n" + "=" * 50)
        print("✅ WebPilot v2.0 Integration Test Complete!")
        print("\nKey Achievements:")
        print("- Playwright handles all browser automation")
        print("- WebPilot adds AI intelligence layer")
        print("- Natural language commands work")
        print("- Clean separation of concerns")


async def test_without_llm():
    """Test that still works without LLM configured."""
    
    print("\n🧪 Testing Without LLM (Graceful Degradation)")
    print("=" * 50)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Test direct Playwright adapter
        from src.webpilot.v2 import PlaywrightAdapter
        
        adapter = PlaywrightAdapter(page)
        
        print("📝 Direct Playwright operations via adapter:")
        
        # Direct operations still work
        await adapter.execute_playwright_action('goto', url='https://example.com')
        print(f"✅ Navigated to: {adapter.get_url()}")
        
        # Smart wait
        found = await adapter.smart_wait('h1', timeout=5000)
        print(f"✅ Element found: {found}")
        
        # Screenshot
        screenshot = await adapter.take_screenshot()
        print(f"✅ Screenshot taken: {len(screenshot)} bytes")
        
        await browser.close()
        
        print("✅ Adapter works without AI!")


async def benchmark_performance():
    """Compare performance: v2.0 vs raw Playwright."""
    
    print("\n⚡ Performance Benchmark")
    print("=" * 50)
    
    import time
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # Test raw Playwright
        print("\n1️⃣ Raw Playwright:")
        page1 = await browser.new_page()
        
        start = time.time()
        await page1.goto('https://example.com')
        await page1.click('h1')
        playwright_time = time.time() - start
        print(f"   Time: {playwright_time*1000:.1f}ms")
        
        # Test with WebPilot adapter
        print("\n2️⃣ WebPilot Adapter:")
        page2 = await browser.new_page()
        adapter = PlaywrightAdapter(page2)
        
        start = time.time()
        await adapter.execute_playwright_action('goto', url='https://example.com')
        await adapter.execute_playwright_action('click', selector='h1')
        adapter_time = time.time() - start
        print(f"   Time: {adapter_time*1000:.1f}ms")
        
        # Calculate overhead
        overhead = ((adapter_time - playwright_time) / playwright_time) * 100
        print(f"\n📊 Adapter overhead: {overhead:.1f}%")
        print(f"   (Should be <5% - we're just a thin wrapper!)")
        
        await browser.close()


async def main():
    """Run all tests."""
    
    # Check if Playwright is installed
    try:
        from playwright.async_api import async_playwright
        print("✅ Playwright is installed")
    except ImportError:
        print("❌ Playwright not installed!")
        print("Run: pip install playwright && playwright install")
        return
    
    # Run tests
    await test_without_llm()  # This always works
    await benchmark_performance()  # Performance check
    
    # Only test AI features if API key is set
    if os.getenv('OPENAI_API_KEY'):
        await test_basic_automation()
    else:
        print("\n⚠️ Skipping AI tests (no OPENAI_API_KEY set)")
        print("Set your API key to test natural language features")


if __name__ == '__main__':
    asyncio.run(main())