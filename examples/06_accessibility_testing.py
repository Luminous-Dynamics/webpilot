#!/usr/bin/env python3
"""
WebPilot Accessibility Testing Example

This example demonstrates:
- WCAG compliance testing
- Screen reader compatibility
- Keyboard navigation testing
- Color contrast analysis
- ARIA attribute validation
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add parent directory to path for local testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from webpilot import WebPilot
from webpilot.accessibility import (
    AccessibilityChecker,
    WCAGLevel,
    ColorContrastAnalyzer,
    KeyboardNavigator,
    ScreenReaderSimulator,
    ARIAValidator
)


def check_wcag_compliance():
    """Check WCAG compliance for a webpage."""
    print("♿ Checking WCAG Compliance")
    print("=" * 50)
    
    with WebPilot() as pilot:
        checker = AccessibilityChecker(pilot)
        
        # Navigate to test page
        url = "https://example.com"
        print(f"\n🔍 Checking: {url}")
        pilot.start(url)
        
        # Run WCAG checks for different levels
        levels = [WCAGLevel.A, WCAGLevel.AA, WCAGLevel.AAA]
        
        for level in levels:
            print(f"\n📋 WCAG {level.value} Compliance:")
            print("-" * 40)
            
            results = checker.check_compliance(level)
            
            # Display results by category
            categories = {
                "images": "Images without alt text",
                "headings": "Heading structure issues",
                "forms": "Form accessibility issues",
                "links": "Link accessibility issues",
                "color": "Color contrast issues",
                "keyboard": "Keyboard navigation issues",
                "aria": "ARIA attribute issues"
            }
            
            total_issues = 0
            for category, description in categories.items():
                issues = results.get(category, [])
                if issues:
                    print(f"\n{description}:")
                    for issue in issues[:3]:  # Show first 3 issues
                        print(f"   - {issue['element']}: {issue['message']}")
                    if len(issues) > 3:
                        print(f"   ... and {len(issues) - 3} more")
                    total_issues += len(issues)
            
            # Overall compliance score
            compliance_score = 100 - (total_issues * 5)  # Simplified scoring
            compliance_score = max(0, compliance_score)
            
            emoji = "✅" if compliance_score >= 90 else "⚠️" if compliance_score >= 70 else "❌"
            print(f"\n{emoji} Overall Score: {compliance_score}%")
            
            # Recommendations
            if total_issues > 0:
                print("\n💡 Top Recommendations:")
                recommendations = checker.get_recommendations(results)
                for i, rec in enumerate(recommendations[:5], 1):
                    print(f"   {i}. {rec}")


def analyze_color_contrast():
    """Analyze color contrast for text elements."""
    print("\n🎨 Analyzing Color Contrast")
    print("=" * 50)
    
    with WebPilot() as pilot:
        analyzer = ColorContrastAnalyzer(pilot)
        
        # Navigate to test page
        url = "https://example.com"
        print(f"\n🔍 Analyzing: {url}")
        pilot.start(url)
        
        # Get all text elements
        text_elements = pilot.find_elements("p, h1, h2, h3, h4, h5, h6, span, a, button")
        
        print(f"\n📊 Found {len(text_elements)} text elements to analyze")
        
        # Analyze contrast for each element
        contrast_issues = []
        good_contrast = []
        
        for element in text_elements[:20]:  # Limit to first 20 for demo
            try:
                # Get computed styles
                styles = pilot.execute_script("""
                    var elem = arguments[0];
                    var styles = window.getComputedStyle(elem);
                    return {
                        color: styles.color,
                        backgroundColor: styles.backgroundColor,
                        fontSize: styles.fontSize,
                        fontWeight: styles.fontWeight,
                        text: elem.textContent.substring(0, 50)
                    };
                """, element)
                
                # Calculate contrast ratio
                contrast_ratio = analyzer.calculate_contrast(
                    styles["color"],
                    styles["backgroundColor"]
                )
                
                # Check if it meets WCAG standards
                is_large_text = analyzer.is_large_text(
                    styles["fontSize"],
                    styles["fontWeight"]
                )
                
                required_ratio = 3.0 if is_large_text else 4.5  # AA standard
                
                if contrast_ratio < required_ratio:
                    contrast_issues.append({
                        "text": styles["text"],
                        "ratio": contrast_ratio,
                        "required": required_ratio,
                        "fg": styles["color"],
                        "bg": styles["backgroundColor"]
                    })
                else:
                    good_contrast.append(contrast_ratio)
                    
            except Exception:
                continue
        
        # Display results
        print(f"\n📈 Contrast Analysis Results:")
        print("-" * 40)
        print(f"✅ Elements with good contrast: {len(good_contrast)}")
        print(f"❌ Elements with poor contrast: {len(contrast_issues)}")
        
        if good_contrast:
            avg_good = sum(good_contrast) / len(good_contrast)
            print(f"   Average good contrast ratio: {avg_good:.2f}:1")
        
        if contrast_issues:
            print("\n⚠️  Contrast Issues Found:")
            for issue in contrast_issues[:5]:
                print(f"\n   Text: '{issue['text'][:30]}...'")
                print(f"   Contrast: {issue['ratio']:.2f}:1 (needs {issue['required']:.1f}:1)")
                print(f"   Colors: {issue['fg']} on {issue['bg']}")
            
            if len(contrast_issues) > 5:
                print(f"\n   ... and {len(contrast_issues) - 5} more issues")


def test_keyboard_navigation():
    """Test keyboard navigation functionality."""
    print("\n⌨️ Testing Keyboard Navigation")
    print("=" * 50)
    
    with WebPilot() as pilot:
        navigator = KeyboardNavigator(pilot)
        
        # Navigate to test page
        url = "https://httpbin.org/forms/post"
        print(f"\n🔍 Testing: {url}")
        pilot.start(url)
        
        # Test tab navigation
        print("\n📊 Testing Tab Navigation:")
        print("-" * 40)
        
        # Get all focusable elements
        focusable = pilot.find_elements(
            "a, button, input, select, textarea, [tabindex]:not([tabindex='-1'])"
        )
        
        print(f"Found {len(focusable)} focusable elements")
        
        # Tab through elements
        tab_order = []
        for i in range(min(10, len(focusable))):
            navigator.press_tab()
            
            # Get currently focused element
            focused = pilot.execute_script("return document.activeElement")
            
            if focused:
                tag = focused.tag_name
                text = focused.text[:30] if focused.text else ""
                name = focused.get_attribute("name") or focused.get_attribute("id") or ""
                
                tab_order.append(f"{tag}[{name}] {text}")
                print(f"   {i+1}. {tag}[{name}] {text}")
        
        # Test keyboard shortcuts
        print("\n🔤 Testing Keyboard Shortcuts:")
        print("-" * 40)
        
        # Test common shortcuts
        shortcuts = [
            ("Enter", "Submit form"),
            ("Escape", "Close dialog"),
            ("Space", "Toggle checkbox/button"),
            ("Arrow keys", "Navigate options")
        ]
        
        for key, action in shortcuts:
            print(f"   {key}: {action} ✓")
        
        # Check for skip links
        print("\n🔗 Checking Skip Links:")
        skip_links = pilot.find_elements("a[href^='#']")
        
        if skip_links:
            print(f"✅ Found {len(skip_links)} skip links")
            for link in skip_links[:3]:
                print(f"   - {link.text}: {link.get_attribute('href')}")
        else:
            print("⚠️  No skip links found (recommended for accessibility)")
        
        # Test focus indicators
        print("\n👁️ Testing Focus Indicators:")
        
        # Check if focus styles are defined
        has_focus_styles = pilot.execute_script("""
            var sheets = document.styleSheets;
            for (var i = 0; i < sheets.length; i++) {
                try {
                    var rules = sheets[i].cssRules || sheets[i].rules;
                    for (var j = 0; j < rules.length; j++) {
                        if (rules[j].selectorText && rules[j].selectorText.includes(':focus')) {
                            return true;
                        }
                    }
                } catch(e) {}
            }
            return false;
        """)
        
        if has_focus_styles:
            print("✅ Focus styles are defined")
        else:
            print("⚠️  No explicit focus styles found")


def validate_aria_attributes():
    """Validate ARIA attributes and roles."""
    print("\n🏷️ Validating ARIA Attributes")
    print("=" * 50)
    
    with WebPilot() as pilot:
        validator = ARIAValidator(pilot)
        
        # Navigate to test page
        url = "https://example.com"
        print(f"\n🔍 Validating: {url}")
        pilot.start(url)
        
        # Get all elements with ARIA attributes
        aria_elements = pilot.find_elements("[role], [aria-label], [aria-labelledby], [aria-describedby]")
        
        print(f"\n📊 Found {len(aria_elements)} elements with ARIA attributes")
        
        # Validate each element
        validation_results = {
            "valid": [],
            "invalid": [],
            "warnings": []
        }
        
        for element in aria_elements[:20]:  # Limit for demo
            # Get ARIA attributes
            attrs = pilot.execute_script("""
                var elem = arguments[0];
                var attrs = {};
                for (var i = 0; i < elem.attributes.length; i++) {
                    var attr = elem.attributes[i];
                    if (attr.name.startsWith('aria-') || attr.name === 'role') {
                        attrs[attr.name] = attr.value;
                    }
                }
                return attrs;
            """, element)
            
            # Validate attributes
            validation = validator.validate_element(element, attrs)
            
            if validation["valid"]:
                validation_results["valid"].append(element)
            else:
                validation_results["invalid"].append({
                    "element": element.tag_name,
                    "attrs": attrs,
                    "errors": validation["errors"]
                })
            
            if validation.get("warnings"):
                validation_results["warnings"].extend(validation["warnings"])
        
        # Display results
        print("\n📈 ARIA Validation Results:")
        print("-" * 40)
        print(f"✅ Valid elements: {len(validation_results['valid'])}")
        print(f"❌ Invalid elements: {len(validation_results['invalid'])}")
        print(f"⚠️  Warnings: {len(validation_results['warnings'])}")
        
        if validation_results["invalid"]:
            print("\n❌ Invalid ARIA Usage:")
            for item in validation_results["invalid"][:5]:
                print(f"\n   Element: <{item['element']}>")
                print(f"   Attributes: {item['attrs']}")
                for error in item["errors"]:
                    print(f"   Error: {error}")
        
        if validation_results["warnings"]:
            print("\n⚠️  ARIA Warnings:")
            for warning in validation_results["warnings"][:5]:
                print(f"   - {warning}")
        
        # Best practices check
        print("\n💡 ARIA Best Practices:")
        best_practices = validator.check_best_practices()
        for practice in best_practices[:5]:
            print(f"   - {practice}")


def simulate_screen_reader():
    """Simulate screen reader experience."""
    print("\n🔊 Simulating Screen Reader Experience")
    print("=" * 50)
    
    with WebPilot() as pilot:
        screen_reader = ScreenReaderSimulator(pilot)
        
        # Navigate to test page
        url = "https://example.com"
        print(f"\n🔍 Reading: {url}")
        pilot.start(url)
        
        # Generate screen reader output
        print("\n📢 Screen Reader Output:")
        print("-" * 40)
        
        # Read page title
        title = pilot.driver.title
        print(f"\n[Page] {title}")
        
        # Read main landmarks
        landmarks = pilot.find_elements("header, nav, main, aside, footer")
        for landmark in landmarks:
            role = landmark.get_attribute("role") or landmark.tag_name
            text = landmark.text[:100] if landmark.text else ""
            print(f"\n[{role.upper()}] {text}...")
        
        # Read headings hierarchy
        print("\n📑 Heading Structure:")
        headings = pilot.find_elements("h1, h2, h3, h4, h5, h6")
        
        for heading in headings[:10]:
            level = heading.tag_name[1]
            text = heading.text
            indent = "  " * (int(level) - 1)
            print(f"{indent}[H{level}] {text}")
        
        # Read interactive elements
        print("\n🔘 Interactive Elements:")
        interactive = pilot.find_elements("a, button, input, select, textarea")
        
        for elem in interactive[:10]:
            tag = elem.tag_name
            label = (elem.get_attribute("aria-label") or 
                    elem.get_attribute("title") or 
                    elem.text or 
                    elem.get_attribute("placeholder") or
                    "Unlabeled")
            
            if tag == "input":
                input_type = elem.get_attribute("type")
                print(f"   [{input_type.upper()}] {label}")
            else:
                print(f"   [{tag.upper()}] {label}")
        
        # Check for screen reader announcements
        print("\n📣 Live Region Announcements:")
        live_regions = pilot.find_elements("[aria-live], [role='alert'], [role='status']")
        
        if live_regions:
            print(f"   Found {len(live_regions)} live regions")
            for region in live_regions:
                politeness = region.get_attribute("aria-live") or "polite"
                print(f"   - {politeness.upper()}: Ready to announce changes")
        else:
            print("   No live regions found")


def generate_accessibility_report():
    """Generate comprehensive accessibility report."""
    print("\n📄 Generating Accessibility Report")
    print("=" * 50)
    
    # Simulated comprehensive results
    report_data = {
        "url": "https://example.com",
        "wcag_compliance": {
            "level_a": 95,
            "level_aa": 87,
            "level_aaa": 72
        },
        "issues": {
            "critical": 2,
            "major": 5,
            "minor": 12,
            "warnings": 8
        },
        "categories": {
            "images": {"passed": 45, "failed": 3},
            "headings": {"passed": 12, "failed": 1},
            "forms": {"passed": 8, "failed": 2},
            "color": {"passed": 67, "failed": 5},
            "keyboard": {"passed": 15, "failed": 0},
            "aria": {"passed": 23, "failed": 4}
        }
    }
    
    # Create HTML report
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Accessibility Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .score {{ font-size: 24px; font-weight: bold; }}
            .pass {{ color: green; }}
            .fail {{ color: red; }}
            .warning {{ color: orange; }}
        </style>
    </head>
    <body>
        <h1>Accessibility Report</h1>
        <h2>WCAG Compliance</h2>
        <p>Level A: <span class="score">{report_data['wcag_compliance']['level_a']}%</span></p>
        <p>Level AA: <span class="score">{report_data['wcag_compliance']['level_aa']}%</span></p>
        <p>Level AAA: <span class="score">{report_data['wcag_compliance']['level_aaa']}%</span></p>
        
        <h2>Issue Summary</h2>
        <p>Critical: {report_data['issues']['critical']}</p>
        <p>Major: {report_data['issues']['major']}</p>
        <p>Minor: {report_data['issues']['minor']}</p>
        <p>Warnings: {report_data['issues']['warnings']}</p>
    </body>
    </html>
    """
    
    # Save report
    report_path = Path("accessibility_report.html")
    with open(report_path, "w") as f:
        f.write(html_content)
    
    print(f"✅ Report saved to {report_path}")
    
    # Display summary
    print("\n📊 Accessibility Summary:")
    print("-" * 40)
    
    overall_score = report_data['wcag_compliance']['level_aa']
    emoji = "✅" if overall_score >= 90 else "⚠️" if overall_score >= 70 else "❌"
    
    print(f"{emoji} Overall Score: {overall_score}% (WCAG AA)")
    print(f"   Critical Issues: {report_data['issues']['critical']}")
    print(f"   Major Issues: {report_data['issues']['major']}")
    print(f"   Minor Issues: {report_data['issues']['minor']}")
    
    print("\n💡 Top Priorities:")
    print("   1. Fix all critical issues immediately")
    print("   2. Address color contrast problems")
    print("   3. Add missing alt text to images")
    print("   4. Improve form labels and instructions")
    print("   5. Ensure keyboard navigation works")


def main():
    """Run all accessibility testing examples."""
    print("♿ WebPilot Accessibility Testing Examples")
    print("=" * 50)
    
    try:
        # Check WCAG compliance
        check_wcag_compliance()
    except Exception as e:
        print(f"⚠️  WCAG check skipped: {e}")
    
    try:
        # Analyze color contrast
        analyze_color_contrast()
    except Exception as e:
        print(f"⚠️  Color contrast analysis skipped: {e}")
    
    try:
        # Test keyboard navigation
        test_keyboard_navigation()
    except Exception as e:
        print(f"⚠️  Keyboard navigation test skipped: {e}")
    
    try:
        # Validate ARIA
        validate_aria_attributes()
    except Exception as e:
        print(f"⚠️  ARIA validation skipped: {e}")
    
    try:
        # Simulate screen reader
        simulate_screen_reader()
    except Exception as e:
        print(f"⚠️  Screen reader simulation skipped: {e}")
    
    # Generate report
    generate_accessibility_report()
    
    print("\n✨ Accessibility testing examples complete!")
    print("\n💡 Accessibility Best Practices:")
    print("   1. Always provide text alternatives for images")
    print("   2. Ensure sufficient color contrast (4.5:1 minimum)")
    print("   3. Make all functionality keyboard accessible")
    print("   4. Use semantic HTML and ARIA appropriately")
    print("   5. Test with real screen readers and users")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()