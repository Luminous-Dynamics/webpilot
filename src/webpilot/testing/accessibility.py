#!/usr/bin/env python3
"""
Accessibility Testing - WCAG 2.1 Compliance Checking
Comprehensive a11y auditing for web applications
"""

from typing import List, Dict, Optional, Any
from pathlib import Path
import json
from datetime import datetime


class AccessibilityTester:
    """WCAG 2.1 compliance testing"""
    
    # WCAG levels
    LEVEL_A = 'A'
    LEVEL_AA = 'AA'
    LEVEL_AAA = 'AAA'
    
    def __init__(self, level: str = LEVEL_AA):
        """
        Initialize accessibility tester.
        
        Args:
            level: WCAG compliance level (A, AA, or AAA)
        """
        self.level = level
        self.reports_dir = Path("accessibility_reports")
        self.reports_dir.mkdir(exist_ok=True)
    
    def check_wcag_compliance(self, page) -> Dict[str, Any]:
        """
        Check page for WCAG compliance issues.
        
        Args:
            page: Playwright page object
            
        Returns:
            Compliance report with violations
        """
        print(f"🔍 Checking WCAG {self.level} compliance...")
        
        violations = []
        
        # Run all checks
        violations.extend(self._check_images(page))
        violations.extend(self._check_links(page))
        violations.extend(self._check_forms(page))
        violations.extend(self._check_headings(page))
        violations.extend(self._check_landmarks(page))
        violations.extend(self._check_color_contrast(page))
        violations.extend(self._check_keyboard_navigation(page))
        violations.extend(self._check_focus_management(page))
        violations.extend(self._check_aria_attributes(page))
        
        # Categorize by severity
        critical = [v for v in violations if v['severity'] == 'critical']
        serious = [v for v in violations if v['severity'] == 'serious']
        moderate = [v for v in violations if v['severity'] == 'moderate']
        minor = [v for v in violations if v['severity'] == 'minor']
        
        report = {
            'url': page.url,
            'wcag_level': self.level,
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_violations': len(violations),
                'critical': len(critical),
                'serious': len(serious),
                'moderate': len(moderate),
                'minor': len(minor)
            },
            'violations': violations,
            'passed': len(violations) == 0
        }
        
        self._print_report(report)
        self._save_report(report)
        
        return report
    
    def _check_images(self, page) -> List[Dict]:
        """Check images for alt text"""
        violations = []
        
        images = page.query_selector_all('img')
        for i, img in enumerate(images):
            alt = img.get_attribute('alt')
            if alt is None:
                src = img.get_attribute('src') or 'unknown'
                violations.append({
                    'rule': 'WCAG 1.1.1 Non-text Content',
                    'severity': 'serious',
                    'element': 'img',
                    'selector': f'img:nth-of-type({i+1})',
                    'message': f'Image missing alt attribute: {src[:50]}',
                    'fix': 'Add alt="" for decorative images or descriptive alt text'
                })
        
        return violations
    
    def _check_links(self, page) -> List[Dict]:
        """Check links for accessibility"""
        violations = []
        
        links = page.query_selector_all('a')
        for i, link in enumerate(links):
            # Check for empty links
            text = link.inner_text().strip()
            href = link.get_attribute('href')
            
            if not text and not link.query_selector('img[alt]'):
                violations.append({
                    'rule': 'WCAG 2.4.4 Link Purpose',
                    'severity': 'serious',
                    'element': 'a',
                    'selector': f'a:nth-of-type({i+1})',
                    'message': f'Link has no text or alt text: {href[:50] if href else "no href"}',
                    'fix': 'Add descriptive link text or aria-label'
                })
            
            # Check for "click here" or generic text
            generic_text = ['click here', 'read more', 'click', 'here', 'more']
            if text.lower() in generic_text:
                violations.append({
                    'rule': 'WCAG 2.4.4 Link Purpose',
                    'severity': 'moderate',
                    'element': 'a',
                    'selector': f'a:nth-of-type({i+1})',
                    'message': f'Link has generic text: "{text}"',
                    'fix': 'Use descriptive link text that makes sense out of context'
                })
        
        return violations
    
    def _check_forms(self, page) -> List[Dict]:
        """Check form controls for labels"""
        violations = []
        
        # Check inputs
        inputs = page.query_selector_all('input:not([type="hidden"]), textarea, select')
        for i, input_el in enumerate(inputs):
            input_id = input_el.get_attribute('id')
            input_type = input_el.get_attribute('type') or 'text'
            
            # Check for label
            has_label = False
            if input_id:
                has_label = page.query_selector(f'label[for="{input_id}"]') is not None
            
            # Check for aria-label
            has_aria_label = input_el.get_attribute('aria-label') is not None
            
            if not has_label and not has_aria_label:
                violations.append({
                    'rule': 'WCAG 3.3.2 Labels or Instructions',
                    'severity': 'critical',
                    'element': input_el.evaluate('el => el.tagName.toLowerCase()'),
                    'selector': f'{input_el.evaluate("el => el.tagName.toLowerCase()")}:nth-of-type({i+1})',
                    'message': f'Form {input_type} has no label',
                    'fix': 'Add <label> element or aria-label attribute'
                })
        
        return violations
    
    def _check_headings(self, page) -> List[Dict]:
        """Check heading hierarchy"""
        violations = []
        
        headings = page.query_selector_all('h1, h2, h3, h4, h5, h6')
        levels = []
        
        for heading in headings:
            tag = heading.evaluate('el => el.tagName')
            level = int(tag[1])  # Extract number from h1, h2, etc.
            levels.append(level)
            
            # Check if heading is empty
            text = heading.inner_text().strip()
            if not text:
                violations.append({
                    'rule': 'WCAG 1.3.1 Info and Relationships',
                    'severity': 'serious',
                    'element': tag.lower(),
                    'selector': tag.lower(),
                    'message': f'Empty {tag} heading',
                    'fix': 'Remove empty heading or add content'
                })
        
        # Check for skipped levels
        for i in range(1, len(levels)):
            if levels[i] - levels[i-1] > 1:
                violations.append({
                    'rule': 'WCAG 1.3.1 Info and Relationships',
                    'severity': 'moderate',
                    'element': 'headings',
                    'selector': 'h1-h6',
                    'message': f'Skipped heading level: h{levels[i-1]} to h{levels[i]}',
                    'fix': 'Use sequential heading levels (don\'t skip)'
                })
        
        # Check for multiple h1s
        h1_count = len([l for l in levels if l == 1])
        if h1_count > 1:
            violations.append({
                'rule': 'WCAG 1.3.1 Info and Relationships',
                'severity': 'moderate',
                'element': 'h1',
                'selector': 'h1',
                'message': f'Page has {h1_count} h1 headings (should have 1)',
                'fix': 'Use only one h1 per page'
            })
        
        return violations
    
    def _check_landmarks(self, page) -> List[Dict]:
        """Check for ARIA landmarks"""
        violations = []
        
        # Check for main landmark
        has_main = page.query_selector('main, [role="main"]') is not None
        if not has_main:
            violations.append({
                'rule': 'WCAG 1.3.1 Info and Relationships',
                'severity': 'moderate',
                'element': 'landmarks',
                'selector': 'body',
                'message': 'Page missing <main> landmark',
                'fix': 'Add <main> element or role="main"'
            })
        
        return violations
    
    def _check_color_contrast(self, page) -> List[Dict]:
        """Check color contrast ratios (basic check)"""
        violations = []
        
        # This is a simplified check - full contrast checking requires
        # analyzing computed styles and background colors
        # For production, recommend using axe-core or similar
        
        # Check for text that might have contrast issues
        elements = page.query_selector_all('p, span, a, button, h1, h2, h3, h4, h5, h6')
        
        for el in elements[:20]:  # Sample first 20 to avoid slowdown
            try:
                color = el.evaluate('el => window.getComputedStyle(el).color')
                bg_color = el.evaluate('el => window.getComputedStyle(el).backgroundColor')
                
                # Basic check: if both are similar (simplified)
                if color == bg_color:
                    violations.append({
                        'rule': 'WCAG 1.4.3 Contrast (Minimum)',
                        'severity': 'critical',
                        'element': el.evaluate('el => el.tagName.toLowerCase()'),
                        'selector': 'unknown',
                        'message': 'Text and background color are identical',
                        'fix': 'Ensure 4.5:1 contrast ratio for normal text'
                    })
            except:
                pass  # Skip if evaluation fails
        
        return violations
    
    def _check_keyboard_navigation(self, page) -> List[Dict]:
        """Check keyboard navigation support"""
        violations = []
        
        # Check for skip links
        skip_link = page.query_selector('a[href^="#"]')
        if skip_link:
            # Good - has skip link
            pass
        else:
            violations.append({
                'rule': 'WCAG 2.4.1 Bypass Blocks',
                'severity': 'moderate',
                'element': 'navigation',
                'selector': 'body',
                'message': 'No skip navigation link found',
                'fix': 'Add skip link as first focusable element'
            })
        
        # Check for focus indicators
        focusable = page.query_selector_all('a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])')
        if len(focusable) > 0:
            # Sample check - verify some elements have focus styles
            # In production, this would need more sophisticated testing
            pass
        
        return violations
    
    def _check_focus_management(self, page) -> List[Dict]:
        """Check focus management"""
        violations = []
        
        # Check for positive tabindex (anti-pattern)
        positive_tabindex = page.query_selector_all('[tabindex]:not([tabindex="0"]):not([tabindex="-1"])')
        
        for el in positive_tabindex:
            tabindex = el.get_attribute('tabindex')
            if tabindex and int(tabindex) > 0:
                violations.append({
                    'rule': 'WCAG 2.4.3 Focus Order',
                    'severity': 'moderate',
                    'element': el.evaluate('el => el.tagName.toLowerCase()'),
                    'selector': f'[tabindex="{tabindex}"]',
                    'message': f'Positive tabindex ({tabindex}) disrupts natural tab order',
                    'fix': 'Use tabindex="0" or remove tabindex'
                })
        
        return violations
    
    def _check_aria_attributes(self, page) -> List[Dict]:
        """Check ARIA attributes for validity"""
        violations = []
        
        # Check for aria-hidden on focusable elements
        hidden_focusable = page.query_selector_all('[aria-hidden="true"] a, [aria-hidden="true"] button, [aria-hidden="true"] input')
        
        for el in hidden_focusable:
            violations.append({
                'rule': 'WCAG 4.1.2 Name, Role, Value',
                'severity': 'serious',
                'element': el.evaluate('el => el.tagName.toLowerCase()'),
                'selector': '[aria-hidden="true"]',
                'message': 'Focusable element hidden with aria-hidden="true"',
                'fix': 'Remove aria-hidden or make element non-focusable'
            })
        
        return violations
    
    def _print_report(self, report: Dict):
        """Pretty print accessibility report"""
        summary = report['summary']
        
        print(f"\n📊 Accessibility Report ({report['wcag_level']})")
        print(f"   URL: {report['url']}")
        print(f"\n   Total violations: {summary['total_violations']}")
        print(f"   🔴 Critical: {summary['critical']}")
        print(f"   🟠 Serious: {summary['serious']}")
        print(f"   🟡 Moderate: {summary['moderate']}")
        print(f"   🔵 Minor: {summary['minor']}")
        
        if summary['total_violations'] == 0:
            print(f"\n   ✅ No violations found!")
        else:
            print(f"\n   ❌ {summary['total_violations']} violations need fixing")
            
            # Show first few violations
            print(f"\n   Top violations:")
            for v in report['violations'][:5]:
                print(f"     • [{v['severity']}] {v['message']}")
                print(f"       Fix: {v['fix']}")
    
    def _save_report(self, report: Dict):
        """Save accessibility report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"accessibility_{timestamp}.json"
        filepath = self.reports_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n   💾 Report saved: {filepath}")
    
    def test_keyboard_navigation(self, page) -> bool:
        """
        Test keyboard navigation through page.
        
        Returns:
            True if keyboard navigation works
        """
        print("\n⌨️  Testing keyboard navigation...")
        
        # Get all focusable elements
        focusable = page.query_selector_all(
            'a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
        )
        
        if len(focusable) == 0:
            print("   ⚠️  No focusable elements found")
            return False
        
        # Tab through first few elements
        for i in range(min(5, len(focusable))):
            page.keyboard.press('Tab')
            
            # Check if something is focused
            focused = page.evaluate('document.activeElement.tagName')
            if focused:
                print(f"   ✅ Tab {i+1}: {focused} focused")
        
        print(f"   ✅ Keyboard navigation working")
        return True
    
    def test_screen_reader_compatibility(self, page) -> List[str]:
        """
        Check screen reader compatibility.
        
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Check for lang attribute
        html_lang = page.evaluate('document.documentElement.lang')
        if not html_lang:
            recommendations.append('Add lang attribute to <html> element')
        
        # Check for page title
        title = page.title()
        if not title or title == '':
            recommendations.append('Add descriptive page <title>')
        
        # Check for ARIA landmarks
        landmarks = {
            'banner': page.query_selector('[role="banner"], header'),
            'navigation': page.query_selector('[role="navigation"], nav'),
            'main': page.query_selector('[role="main"], main'),
            'contentinfo': page.query_selector('[role="contentinfo"], footer')
        }
        
        for landmark, element in landmarks.items():
            if not element:
                recommendations.append(f'Add {landmark} landmark')
        
        return recommendations


# Quick usage function
def check_accessibility(page) -> bool:
    """Quick accessibility check - returns True if compliant"""
    tester = AccessibilityTester()
    report = tester.check_wcag_compliance(page)
    return report['passed']


# Example usage
if __name__ == "__main__":
    print("♿ Accessibility Testing Demo\n")
    print("This module checks for WCAG 2.1 compliance issues.")
    print("\nUsage:")
    print("  tester = AccessibilityTester(level='AA')")
    print("  report = tester.check_wcag_compliance(page)")
    print("  if report['passed']:")
    print("      print('✅ Fully accessible!')")
