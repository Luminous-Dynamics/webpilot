#!/usr/bin/env python3
"""
Example 1: Natural Language Test Writing
Write tests in plain English - no selectors needed!
"""

import asyncio
from playwright.async_api import async_playwright
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.webpilot.v2 import AIWebPilot, WebPilotConfig


async def test_e_commerce_checkout():
    """Test an e-commerce site using natural language."""
    
    print("🛍️ E-Commerce Checkout Test (Natural Language)")
    print("=" * 50)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Configure AI pilot
        config = WebPilotConfig(
            llm_provider="openai",
            auto_heal=True,
            verbose=True
        )
        pilot = AIWebPilot(page, config)
        
        # Write test in plain English!
        test_steps = [
            "Go to https://demo.opencart.com",
            "Search for 'MacBook'",
            "Click on the first MacBook product",
            "Add the product to cart",
            "Go to the shopping cart",
            "Verify the MacBook is in the cart",
            "Take a screenshot of the cart"
        ]
        
        print("\n📝 Executing Natural Language Test:")
        for i, step in enumerate(test_steps, 1):
            print(f"\nStep {i}: {step}")
            try:
                result = await pilot.execute(step)
                print(f"✅ {result}")
            except Exception as e:
                print(f"❌ Failed: {e}")
                # AI will try to self-heal!
                if config.auto_heal:
                    print("🔧 Attempting self-healing...")
                    result = await pilot.heal_and_retry(step)
                    print(f"✅ Healed: {result}")
        
        await browser.close()
        
        print("\n" + "=" * 50)
        print("✨ No selectors needed - just describe what to do!")


async def test_form_validation():
    """Test form validation with natural language assertions."""
    
    print("\n📋 Form Validation Test (AI Assertions)")
    print("=" * 50)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        pilot = AIWebPilot(page)
        
        # Natural language testing
        await pilot.execute("Navigate to https://demoqa.com/automation-practice-form")
        
        # Fill form with natural descriptions
        await pilot.execute("Enter 'John' in the first name field")
        await pilot.execute("Enter 'Doe' in the last name field")
        await pilot.execute("Enter 'john@example.com' in the email field")
        await pilot.execute("Select 'Male' for gender")
        await pilot.execute("Enter '1234567890' in the mobile number field")
        
        # Natural language assertions
        assertions = [
            "The form should have a submit button",
            "The first name field should contain 'John'",
            "The email field should be valid",
            "There should be no error messages visible"
        ]
        
        print("\n🔍 Running AI Assertions:")
        for assertion in assertions:
            result = await pilot.assert_visual(assertion)
            status = "✅" if result.passed else "❌"
            print(f"{status} {assertion}")
            if result.explanation:
                print(f"   → {result.explanation}")
        
        await browser.close()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("   WebPilot v2.0: Natural Language Testing")
    print("=" * 60)
    print("\n🚀 Write tests in English, not code!")
    
    asyncio.run(test_e_commerce_checkout())
    asyncio.run(test_form_validation())
    
    print("\n💡 Key Benefits:")
    print("• No need to learn selectors")
    print("• Tests read like documentation")
    print("• AI understands context and intent")
    print("• Self-healing when UI changes")
    print("\n✨ Testing made human-friendly!")