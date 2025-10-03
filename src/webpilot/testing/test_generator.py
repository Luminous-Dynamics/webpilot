#!/usr/bin/env python3
"""
Test Generator - Convert user stories to executable test code
Automatically generates Playwright tests from natural language descriptions
"""

import re
from typing import List, Dict, Optional
from pathlib import Path


class TestGenerator:
    """Generate executable tests from user stories"""
    
    def __init__(self):
        """Initialize test generator"""
        self.test_templates = self._load_templates()
        self.action_patterns = self._load_action_patterns()
    
    def _load_templates(self) -> Dict:
        """Load test code templates"""
        return {
            'test_file': '''#!/usr/bin/env python3
"""
{description}
Generated from user story
"""

from playwright.sync_api import Page, expect

def test_{test_name}(page: Page):
    """
    {user_story}
    """
{test_body}
''',
            'navigate': '    page.goto("{url}")',
            'click': '    page.click("{selector}")',
            'fill': '    page.fill("{selector}", "{value}")',
            'assert_visible': '    expect(page.locator("{selector}")).to_be_visible()',
            'assert_text': '    expect(page.locator("{selector}")).to_contain_text("{text}")',
            'wait': '    page.wait_for_timeout({ms})',
            'screenshot': '    page.screenshot(path="{path}")'
        }
    
    def _load_action_patterns(self) -> Dict:
        """Load patterns for recognizing actions"""
        return {
            'navigate': [
                r'(?:go to|visit|navigate to|open)\s+(.+)',
                r'(?:on|at)\s+(.+?)(?:\s+page)?',
            ],
            'click': [
                r'click(?:\s+on)?\s+(?:the\s+)?(.+)',
                r'press(?:\s+the)?\s+(.+)\s+button',
                r'select\s+(.+)',
            ],
            'type': [
                r'(?:type|enter|fill|input)\s+["\']([^"\']+)["\'](?:\s+in(?:to)?\s+(?:the\s+)?(.+))?',
                r'(?:type|enter|fill)\s+(?:the\s+)?(.+?)\s+(?:field|input|box)\s+with\s+["\']([^"\']+)["\']',
            ],
            'verify': [
                r'(?:should|verify|check|ensure)\s+(?:that\s+)?(?:I\s+)?(?:can\s+)?see\s+(.+)',
                r'(?:should|must)\s+(?:show|display|contain)\s+(.+)',
                r'(?:the\s+)?(.+?)\s+should\s+be\s+visible',
            ],
            'wait': [
                r'wait\s+(?:for\s+)?(\d+)\s*(?:seconds?|s|ms|milliseconds?)?',
            ]
        }
    
    def generate_from_user_story(self, user_story: str, test_name: Optional[str] = None) -> str:
        """
        Generate complete test file from user story.
        
        Args:
            user_story: Natural language description
            test_name: Optional test name (generated if not provided)
            
        Returns:
            Complete Python test code
        """
        # Parse user story into steps
        steps = self._parse_user_story(user_story)
        
        # Generate test name
        if not test_name:
            test_name = self._generate_test_name(user_story)
        
        # Generate test body
        test_body = self._generate_test_body(steps)
        
        # Fill template
        test_code = self.test_templates['test_file'].format(
            description=user_story,
            test_name=test_name,
            user_story=user_story,
            test_body=test_body
        )
        
        return test_code
    
    def _parse_user_story(self, story: str) -> List[Dict]:
        """Parse user story into structured steps"""
        steps = []
        
        # Split by common delimiters
        lines = re.split(r'[.\n]', story)
        lines = [l.strip() for l in lines if l.strip()]
        
        for line in lines:
            step = self._parse_line(line)
            if step:
                steps.append(step)
        
        return steps
    
    def _parse_line(self, line: str) -> Optional[Dict]:
        """Parse a single line into a test step"""
        line_lower = line.lower().strip()
        
        # Try each action type
        for action_type, patterns in self.action_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, line_lower)
                if match:
                    return self._create_step(action_type, match, line)
        
        return None
    
    def _create_step(self, action_type: str, match, original_line: str) -> Dict:
        """Create step from regex match"""
        if action_type == 'navigate':
            url = match.group(1).strip()
            if not url.startswith('http'):
                url = f'http://localhost:3000'
            return {
                'action': 'navigate',
                'url': url,
                'original': original_line
            }
        
        elif action_type == 'click':
            target = match.group(1).strip()
            return {
                'action': 'click',
                'selector': self._target_to_selector(target),
                'target': target,
                'original': original_line
            }
        
        elif action_type == 'type':
            if match.lastindex >= 2:
                text = match.group(1).strip()
                field = match.group(2).strip() if match.group(2) else 'input'
            else:
                text = match.group(2).strip() if match.lastindex >= 2 else ''
                field = match.group(1).strip()
            
            return {
                'action': 'fill',
                'selector': self._target_to_selector(field),
                'value': text,
                'target': field,
                'original': original_line
            }
        
        elif action_type == 'verify':
            expected = match.group(1).strip()
            return {
                'action': 'assert_visible',
                'selector': self._target_to_selector(expected),
                'expected': expected,
                'original': original_line
            }
        
        elif action_type == 'wait':
            duration = int(match.group(1))
            return {
                'action': 'wait',
                'ms': duration * 1000,  # Convert to ms
                'original': original_line
            }
        
        return {
            'action': 'unknown',
            'original': original_line
        }
    
    def _target_to_selector(self, target: str) -> str:
        """Convert target description to Playwright selector"""
        target_lower = target.lower().strip()
        
        # Remove common articles
        target_clean = re.sub(r'\b(the|a|an)\b\s+', '', target_lower)
        
        # Check if it looks like a CSS selector
        if any(c in target for c in ['#', '.', '[', '>']):
            return target
        
        # Check if it's a button
        if 'button' in target_lower:
            button_text = re.sub(r'\s+button', '', target_clean)
            return f'role=button[name=/{button_text}/i]'
        
        # Check if it's a link
        if 'link' in target_lower:
            link_text = re.sub(r'\s+link', '', target_clean)
            return f'role=link[name=/{link_text}/i]'
        
        # Check if it's an input
        if any(word in target_lower for word in ['field', 'input', 'textbox', 'email', 'password']):
            field_name = re.sub(r'\s+(field|input|textbox|box)', '', target_clean)
            return f'[placeholder*="{field_name}"], [name*="{field_name}"], [id*="{field_name}"]'
        
        # Default: text selector
        return f'text=/{target_clean}/i'
    
    def _generate_test_body(self, steps: List[Dict]) -> str:
        """Generate test body code from steps"""
        lines = []
        
        for step in steps:
            action = step['action']
            
            if action == 'navigate':
                lines.append(self.test_templates['navigate'].format(url=step['url']))
            
            elif action == 'click':
                lines.append(self.test_templates['click'].format(selector=step['selector']))
            
            elif action == 'fill':
                lines.append(self.test_templates['fill'].format(
                    selector=step['selector'],
                    value=step['value']
                ))
            
            elif action == 'assert_visible':
                lines.append(self.test_templates['assert_visible'].format(
                    selector=step['selector']
                ))
            
            elif action == 'wait':
                lines.append(self.test_templates['wait'].format(ms=step['ms']))
            
            elif action == 'unknown':
                lines.append(f'    # TODO: {step["original"]}')
        
        return '\n'.join(lines)
    
    def _generate_test_name(self, user_story: str) -> str:
        """Generate test name from user story"""
        # Extract key words
        words = re.findall(r'\b[a-z]+\b', user_story.lower())
        
        # Remove common words
        stop_words = {'a', 'an', 'the', 'to', 'and', 'or', 'but', 'in', 'on', 'at', 'should', 'can', 'be', 'is'}
        words = [w for w in words if w not in stop_words]
        
        # Take first 4-5 words
        name_words = words[:5]
        
        return '_'.join(name_words) if name_words else 'generated_test'
    
    def generate_from_manual_session(self, page) -> str:
        """
        Generate test code from recording manual actions.
        (This would require browser instrumentation - simplified version)
        
        Returns:
            Test code based on recorded actions
        """
        # This is a placeholder - actual implementation would need
        # to instrument the browser and record user actions
        
        return """# Manual session recording not yet implemented
# Use generate_from_user_story() instead"""
    
    def save_test(self, test_code: str, filename: str = "generated_test.py"):
        """Save generated test to file"""
        test_path = Path("tests") / filename
        test_path.parent.mkdir(exist_ok=True)
        
        with open(test_path, 'w') as f:
            f.write(test_code)
        
        print(f"✅ Test saved: {test_path}")
        return str(test_path)
    
    def generate_multiple_tests(self, user_stories: List[str]) -> Dict[str, str]:
        """
        Generate multiple tests from multiple user stories.
        
        Returns:
            Dictionary of test_name -> test_code
        """
        tests = {}
        
        for i, story in enumerate(user_stories):
            test_name = self._generate_test_name(story)
            
            # Ensure unique names
            if test_name in tests:
                test_name = f"{test_name}_{i}"
            
            test_code = self.generate_from_user_story(story, test_name)
            tests[test_name] = test_code
        
        return tests


# Quick usage functions
def generate_test(user_story: str) -> str:
    """Quick function to generate test from user story"""
    generator = TestGenerator()
    return generator.generate_from_user_story(user_story)


def save_test_file(user_story: str, filename: str = "generated_test.py") -> str:
    """Generate and save test file"""
    generator = TestGenerator()
    test_code = generator.generate_from_user_story(user_story)
    return generator.save_test(test_code, filename)


# Example usage
if __name__ == "__main__":
    print("🧪 Test Generator Demo\n")
    
    # Example user story
    user_story = """
    As a user, I want to sign in to see my dashboard.
    Go to http://localhost:3000.
    Click the sign in button.
    Enter "test@example.com" in the email field.
    Enter "password123" in the password field.
    Click submit.
    Verify that I can see "Welcome" on the dashboard.
    """
    
    generator = TestGenerator()
    test_code = generator.generate_from_user_story(user_story)
    
    print("Generated Test:")
    print("=" * 60)
    print(test_code)
    print("=" * 60)
    
    # Save to file
    generator.save_test(test_code, "test_login.py")
    
    print("\n✨ Test generation complete!")
    print("\nUsage:")
    print('  generator = TestGenerator()')
    print('  test = generator.generate_from_user_story("As a user...")')
    print('  generator.save_test(test, "test_feature.py")')
