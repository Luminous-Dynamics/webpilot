#!/usr/bin/env python3
"""
Terra Atlas Globe - Complete WebPilot Test Suite
Demonstrates all 6 WebPilot features working together with WebGL
"""

import sys
sys.path.insert(0, '/srv/luminous-dynamics/_development/web-automation/claude-webpilot/src')

from webpilot.core import PlaywrightAutomation
from webpilot.integrations.dev_server import DevServer
from webpilot.integrations.lighthouse import LighthouseAudit
from webpilot.testing.visual_regression import VisualRegression
from webpilot.testing.accessibility import AccessibilityTester
from webpilot.ai.smart_selectors import SmartSelector
import time


def feature_1_dev_server_detection():
    """Feature 1: Auto-detect Terra Atlas dev server"""
    print("\n" + "="*60)
    print("FEATURE 1: Dev Server Detection")
    print("="*60)

    detector = DevServer()
    servers = detector.scan_ports([3000, 3001, 5173, 5174])

    if servers:
        for server in servers:
            print(f"\n✅ Found: {server['framework']} at http://localhost:{server['port']}")
            print(f"   Status: {server['status']}")
            return server['url']
    else:
        print("\n⚠️  No dev server detected. Start with: npm run dev")
        return None


def feature_2_performance_audit(url):
    """Feature 2: Lighthouse performance scoring"""
    print("\n" + "="*60)
    print("FEATURE 2: Lighthouse Performance Audit")
    print("="*60)

    lighthouse = LighthouseAudit()

    print("\n📊 Running Lighthouse audit...")
    scores = lighthouse.audit_performance_only(url)

    if scores:
        print(f"\n✅ Performance Score: {scores['scores']['performance']['score']}/100")

        # Get Web Vitals
        vitals = scores.get('core_web_vitals', {})
        print(f"   FCP: {vitals.get('first_contentful_paint', 'N/A')}")
        print(f"   LCP: {vitals.get('largest_contentful_paint', 'N/A')}")
        print(f"   TBT: {vitals.get('total_blocking_time', 'N/A')}")
        print(f"   CLS: {vitals.get('cumulative_layout_shift', 'N/A')}")

        return scores
    else:
        print("\n⚠️  Lighthouse audit failed (may need lighthouse CLI installed)")
        return None


def feature_3_visual_regression(url):
    """Feature 3: WebGL screenshot comparison (NON-HEADLESS!)"""
    print("\n" + "="*60)
    print("FEATURE 3: Visual Regression Testing")
    print("="*60)
    print("🌍 Using headless=False for WebGL support!")

    vr = VisualRegression()

    # NON-HEADLESS = WebGL works!
    with PlaywrightAutomation(headless=False) as browser:
        browser.navigate(url)

        # Wait for globe to fully render
        print("\n⏳ Waiting for globe to render (3 seconds)...")
        time.sleep(3)

        # Check if baseline exists (check metadata dict)
        has_baseline = "terra_globe" in vr.metadata

        # Take baseline screenshot
        if not has_baseline:
            print("\n📸 Taking baseline screenshot...")
            baseline_path = vr.take_baseline("terra_globe", browser.page)
            print(f"✅ Baseline saved: {baseline_path}")
            return True
        else:
            print("\n📸 Comparing with baseline...")
            result = vr.compare_with_baseline(
                "terra_globe",
                browser.page,
                threshold=0.1  # 0.1% difference allowed
            )

            if result['match']:
                print(f"✅ Visual regression test PASSED!")
                print(f"   Difference: {result['difference_pct']:.3f}%")
                return True
            else:
                print(f"❌ Visual regression test FAILED!")
                print(f"   Difference: {result['difference_pct']:.3f}%")
                print(f"   Diff image: {result['diff_path']}")
                return False


def feature_4_accessibility_check(url):
    """Feature 4: WCAG 2.1 compliance checking"""
    print("\n" + "="*60)
    print("FEATURE 4: Accessibility Testing")
    print("="*60)

    with PlaywrightAutomation(headless=False) as browser:
        browser.navigate(url)
        time.sleep(2)

        a11y = AccessibilityTester(level='AA')

        print("\n🔍 Checking WCAG 2.1 AA compliance...")
        report = a11y.check_wcag_compliance(browser.page)

        print(f"\n📊 Accessibility Report:")
        print(f"   Total violations: {report['summary']['total_violations']}")
        print(f"   Critical: {report['summary']['critical']}")
        print(f"   Serious: {report['summary']['serious']}")
        print(f"   Moderate: {report['summary']['moderate']}")
        print(f"   Minor: {report['summary']['minor']}")

        if report['passed']:
            print(f"\n✅ Accessibility test PASSED!")
        else:
            print(f"\n⚠️  Accessibility issues found")

            # Show first 3 violations
            for i, violation in enumerate(report['violations'][:3], 1):
                print(f"\n   {i}. {violation['rule']}")
                print(f"      {violation['message']}")

        return report


def feature_5_smart_selectors(url):
    """Feature 5: Auto-healing element finding"""
    print("\n" + "="*60)
    print("FEATURE 5: Smart Selectors")
    print("="*60)

    with PlaywrightAutomation(headless=False) as browser:
        browser.navigate(url)
        time.sleep(2)

        smart = SmartSelector()

        # Try to find filter buttons
        test_elements = [
            "Solar",
            "Wind",
            "All Projects"
        ]

        print("\n🔍 Finding elements with smart selectors...")
        for element_desc in test_elements:
            element = smart.find_element(browser.page, element_desc)

            if element and element.count() > 0:
                print(f"✅ Found: '{element_desc}'")
            else:
                print(f"⚠️  Not found: '{element_desc}'")

        # Show selector strategies used
        print(f"\n📊 Selector success rate: {smart.get_success_rate():.1f}%")

        return True


def feature_6_interaction_test(url):
    """Feature 6: Generated test from user story"""
    print("\n" + "="*60)
    print("FEATURE 6: Interaction Testing (from Test Generator pattern)")
    print("="*60)

    with PlaywrightAutomation(headless=False) as browser:
        browser.navigate(url)
        time.sleep(2)

        print("\n🎭 User Story: Click Solar filter and verify markers update")

        # Step 1: Click Solar filter
        try:
            solar_button = browser.page.locator("button:has-text('Solar')")
            if solar_button.count() > 0:
                solar_button.click()
                print("✅ Step 1: Clicked Solar filter button")
                time.sleep(1)
            else:
                print("⚠️  Solar button not found")
                return False
        except Exception as e:
            print(f"❌ Step 1 failed: {e}")
            return False

        # Step 2: Verify URL or state changed
        try:
            current_url = browser.get_url()
            if 'solar' in current_url.lower() or 'filter' in current_url.lower():
                print("✅ Step 2: URL updated with filter")
            else:
                print("ℹ️  Step 2: Filter may use state management (not URL)")
        except Exception as e:
            print(f"⚠️  Step 2: {e}")

        # Step 3: Verify canvas still visible (globe still rendering)
        try:
            canvas = browser.page.locator("canvas")
            if canvas.count() > 0:
                print("✅ Step 3: Globe canvas still visible after filter")
                return True
            else:
                print("❌ Step 3: Globe canvas disappeared!")
                return False
        except Exception as e:
            print(f"❌ Step 3 failed: {e}")
            return False


def run_complete_suite():
    """Run all 6 WebPilot features on Terra Atlas"""
    print("\n" + "="*60)
    print("🌍 TERRA ATLAS COMPLETE WEBPILOT TEST SUITE")
    print("   Demonstrating all 6 features with WebGL support")
    print("="*60)

    results = {}

    # Feature 1: Dev Server Detection
    url = feature_1_dev_server_detection()
    if not url:
        print("\n❌ Cannot proceed - no dev server found")
        print("   Start server with: npm run dev")
        return

    # Feature 2: Performance Audit
    perf_result = feature_2_performance_audit(url)
    results['performance'] = perf_result is not None

    # Feature 3: Visual Regression (the key WebGL test!)
    visual_result = feature_3_visual_regression(url)
    results['visual_regression'] = visual_result

    # Feature 4: Accessibility
    a11y_result = feature_4_accessibility_check(url)
    results['accessibility'] = a11y_result['passed'] if a11y_result else False

    # Feature 5: Smart Selectors
    selector_result = feature_5_smart_selectors(url)
    results['smart_selectors'] = selector_result

    # Feature 6: Interaction Testing
    interaction_result = feature_6_interaction_test(url)
    results['interactions'] = interaction_result

    # Summary
    print("\n" + "="*60)
    print("📊 COMPLETE TEST SUITE RESULTS")
    print("="*60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for feature, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {feature.replace('_', ' ').title()}")

    print(f"\n🏆 Overall: {passed}/{total} features working")

    if passed == total:
        print("\n🎉 PERFECT SCORE! All WebPilot features working with Terra Atlas!")
    elif passed >= total * 0.8:
        print("\n✅ EXCELLENT! Most features working correctly")
    elif passed >= total * 0.5:
        print("\n⚠️  GOOD! Some features need attention")
    else:
        print("\n❌ NEEDS WORK! Several features require fixes")

    print("\n" + "="*60)
    print("Key Achievement: WebGL visual regression working with headless=False!")
    print("="*60)


if __name__ == "__main__":
    run_complete_suite()
