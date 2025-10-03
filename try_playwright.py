#!/usr/bin/env python3
"""
Quick Playwright demo - see the difference!
Run this to see why Playwright is better.
"""

from playwright.sync_api import sync_playwright
import time

def demo_playwright():
    """5-minute demo showing Playwright advantages."""

    print("🚀 Playwright Demo - See the Difference!\n")

    with sync_playwright() as p:
        # Launch browser (auto-downloads driver if needed!)
        print("1. Launching Firefox...")
        browser = p.firefox.launch(headless=False)
        page = browser.new_page()

        # Navigate (auto-waits for page load!)
        print("2. Navigating to GitHub...")
        page.goto("https://github.com")

        # Take screenshot (no complex setup!)
        print("3. Taking screenshot...")
        page.screenshot(path="screenshots/github_playwright.png")
        print(f"   ✅ Saved to screenshots/github_playwright.png")

        # Get title (simple!)
        title = page.title()
        print(f"4. Page title: {title}")

        # Click using text (Playwright understands human language!)
        print("5. Clicking 'Sign in' button using text selector...")
        try:
            page.click("text=Sign in", timeout=5000)
            print("   ✅ Clicked! (auto-waited for element)")
        except:
            print("   ℹ️  No 'Sign in' button (page layout changed)")

        # Navigate back
        print("6. Going back...")
        page.go_back()

        # Get all links (easy!)
        print("7. Finding all navigation links...")
        links = page.query_selector_all("nav a")
        print(f"   Found {len(links)} navigation links")

        # Execute JavaScript (seamless!)
        print("8. Running JavaScript to get page stats...")
        stats = page.evaluate("""() => ({
            links: document.querySelectorAll('a').length,
            images: document.querySelectorAll('img').length,
            buttons: document.querySelectorAll('button').length
        })""")
        print(f"   Links: {stats['links']}, Images: {stats['images']}, Buttons: {stats['buttons']}")

        # Network interception (Selenium can't do this!)
        print("\n9. 🌟 BONUS: Network interception (Selenium can't do this!)")
        page2 = browser.new_page()

        requests = []
        def log_request(request):
            requests.append({
                'method': request.method,
                'url': request.url,
                'type': request.resource_type
            })

        page2.on("request", log_request)
        page2.goto("https://github.com")

        print(f"   Intercepted {len(requests)} network requests:")
        for req in requests[:5]:  # Show first 5
            print(f"   - {req['method']} {req['type']}: {req['url'][:60]}...")

        print("\n10. Taking final screenshot with trace...")
        page2.screenshot(path="screenshots/github_with_network.png")

        print("\n✨ Demo complete! Check screenshots/ folder.")
        print("\nKey advantages shown:")
        print("  ✅ Auto-waiting - no manual WebDriverWait")
        print("  ✅ Text selectors - 'text=Sign in' just works")
        print("  ✅ Network interception - see all requests")
        print("  ✅ Clean API - less code, more power")
        print("  ✅ Auto driver management - no manual downloads")

        # Clean up
        time.sleep(2)  # Let you see the browser
        browser.close()


def compare_code():
    """Show code comparison."""
    print("\n" + "="*60)
    print("CODE COMPARISON: Selenium vs Playwright")
    print("="*60 + "\n")

    print("SELENIUM (old way):")
    print("-" * 60)
    print("""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 11 lines just to click a button!
driver = webdriver.Firefox()
driver.get("https://github.com")
wait = WebDriverWait(driver, 10)
element = wait.until(
    EC.element_to_be_clickable((By.XPATH, "//a[text()='Sign in']"))
)
element.click()
driver.quit()
    """)

    print("\nPLAYWRIGHT (new way):")
    print("-" * 60)
    print("""
from playwright.sync_api import sync_playwright

# 6 lines - 45% less code!
with sync_playwright() as p:
    browser = p.firefox.launch()
    page = browser.new_page()
    page.goto("https://github.com")
    page.click("text=Sign in")  # Auto-waits!
    browser.close()
    """)

    print("\nKEY DIFFERENCES:")
    print("-" * 60)
    print("  🎯 Playwright: page.click('text=Sign in')")
    print("     Selenium:  wait.until(EC.element_to_be_clickable((By.XPATH, ...)))")
    print("\n  ⚡ Playwright: Auto-waits automatically")
    print("     Selenium:  Manual WebDriverWait everywhere")
    print("\n  🧹 Playwright: 6 lines of code")
    print("     Selenium:  11 lines of code")
    print("\n  📝 Playwright: Human-readable text selectors")
    print("     Selenium:  Complex XPath/CSS selectors")


if __name__ == "__main__":
    try:
        demo_playwright()
        compare_code()

        print("\n" + "="*60)
        print("🎉 RECOMMENDATION: Migrate to Playwright!")
        print("="*60)
        print("\nNext steps:")
        print("  1. Read PLAYWRIGHT_MIGRATION_PLAN.md")
        print("  2. Create playwright_automation.py")
        print("  3. Start migrating features")
        print("\nSee ASSESSMENT_AND_RECOMMENDATIONS.md for full analysis.")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure Playwright is installed:")
        print("  pip install playwright")
        print("  playwright install firefox")
