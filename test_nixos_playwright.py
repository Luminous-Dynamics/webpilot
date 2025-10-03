#!/usr/bin/env python3
"""Test if NixOS native Playwright can launch browsers"""

from playwright.sync_api import sync_playwright

print("🧪 Testing NixOS Native Playwright...")
print()

try:
    with sync_playwright() as p:
        print("✅ Playwright context created")

        # Try to launch Firefox
        print("🦊 Launching Firefox...")
        browser = p.firefox.launch(headless=True)
        print("✅ Firefox launched successfully!")

        page = browser.new_page()
        print("✅ Page created")

        page.goto("https://example.com")
        print(f"✅ Navigated to example.com")
        print(f"   Title: {page.title()}")

        browser.close()
        print("✅ Browser closed")

        print()
        print("🎉 SUCCESS! NixOS native Playwright WORKS!")

except Exception as e:
    print(f"❌ Failed: {e}")
    print()
    print("💡 Recommendation: Use Docker for Playwright on NixOS")
