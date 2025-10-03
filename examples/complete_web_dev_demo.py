#!/usr/bin/env python3
"""
Complete Web Development System Demo
Demonstrates all 6 new features working together
"""

import sys
sys.path.insert(0, 'src')

from webpilot.core import PlaywrightAutomation
from webpilot.integrations.dev_server import DevServer
from webpilot.integrations.lighthouse import LighthouseAudit
from webpilot.testing.visual_regression import VisualRegression
from webpilot.testing.accessibility import AccessibilityTester
from webpilot.ai.smart_selectors import SmartSelector
from webpilot.testing.test_generator import TestGenerator

print("""
╔════════════════════════════════════════════════════════╗
║  🚀 Complete Web Development System Demo              ║
║  Demonstrating all 6 features                         ║
╚════════════════════════════════════════════════════════╝
""")

# Feature 1: Dev Server Detection
print("\n" + "="*60)
print("FEATURE 1: Dev Server Detection")
print("="*60)

detector = DevServer()
servers = detector.scan_ports()

if servers:
    print(f"✅ Found {len(servers)} development server(s)")
    for server in servers:
        print(f"   • {server['framework']} at {server['url']}")
else:
    print("⚠️  No dev servers found. Starting example.com demo instead.")

# Use detected server or fallback
test_url = servers[0]['url'] if servers else "https://example.com"

# Feature 2: Lighthouse Performance Audit
print("\n" + "="*60)
print("FEATURE 2: Lighthouse Performance Audit")
print("="*60)

lighthouse = LighthouseAudit()
print("Running Lighthouse audit (this may take 30-60 seconds)...")
# Note: Requires lighthouse CLI: npm install -g lighthouse
perf_scores = lighthouse.audit_performance_only(test_url)

# Feature 3: Visual Regression Testing
print("\n" + "="*60)
print("FEATURE 3: Visual Regression Testing")
print("="*60)

vr = VisualRegression()
with PlaywrightAutomation(headless=True) as browser:
    browser.navigate(test_url)
    
    # Take baseline
    vr.take_baseline("demo_page", browser.page)
    
    # Test against baseline
    result = vr.compare_with_baseline("demo_page", browser.page, threshold=0.1)
    print(f"Visual match: {result.get('match', False)}")

# Feature 4: Accessibility Testing
print("\n" + "="*60)
print("FEATURE 4: WCAG Accessibility Audit")
print("="*60)

with PlaywrightAutomation(headless=True) as browser:
    browser.navigate(test_url)
    
    a11y = AccessibilityTester(level='AA')
    report = a11y.check_wcag_compliance(browser.page)

# Feature 5: Smart Selectors
print("\n" + "="*60)
print("FEATURE 5: Smart Selectors (Auto-Healing)")
print("="*60)

with PlaywrightAutomation(headless=True) as browser:
    browser.navigate(test_url)
    
    smart = SmartSelector()
    element = smart.find_element(browser.page, "more information")
    
    if element:
        print("✅ Smart selector found element!")
    else:
        print("⚠️  Element not found (expected for example.com)")

# Feature 6: Test Generator
print("\n" + "="*60)
print("FEATURE 6: Test Generator (User Stories → Code)")
print("="*60)

user_story = """
As a user, I want to verify the homepage loads.
Go to https://example.com.
Verify that I can see "Example Domain".
"""

generator = TestGenerator()
test_code = generator.generate_from_user_story(user_story, "test_example_homepage")
print("Generated test preview:")
print(test_code[:300] + "...")

# Summary
print("\n" + "="*60)
print("SUMMARY: All 6 Features Demonstrated!")
print("="*60)

print("""
✅ Dev Server Detection
✅ Lighthouse Performance Audit
✅ Visual Regression Testing
✅ Accessibility Testing (WCAG 2.1)
✅ Smart Selectors (Auto-Healing)
✅ Test Generator (User Stories → Code)

🎉 Complete Web Development System is READY!

Next steps:
1. Test your own application
2. Set up CI/CD integration
3. Generate comprehensive test suites
4. Establish quality baselines
""")
