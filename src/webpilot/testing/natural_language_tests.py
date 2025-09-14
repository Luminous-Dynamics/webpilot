"""
Natural Language Test Generation for WebPilot

Converts natural language test descriptions into executable test code.
Supports multiple test frameworks and languages.
"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import textwrap

from ..core import WebPilot
from ..intelligence.autonomous_agent import AutonomousAgent, TaskPlan
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class TestFramework(Enum):
    """Supported test frameworks."""
    PYTEST = "pytest"
    UNITTEST = "unittest"
    JEST = "jest"
    MOCHA = "mocha"
    PLAYWRIGHT = "playwright"
    CYPRESS = "cypress"
    SELENIUM = "selenium"


class Language(Enum):
    """Supported programming languages."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CSHARP = "csharp"


@dataclass
class TestCase:
    """Represents a single test case."""
    name: str
    description: str
    steps: List[Dict[str, Any]]
    assertions: List[Dict[str, Any]]
    setup: Optional[List[Dict[str, Any]]] = None
    teardown: Optional[List[Dict[str, Any]]] = None
    tags: List[str] = field(default_factory=list)
    data: Optional[Dict[str, Any]] = None


@dataclass
class TestSuite:
    """Collection of test cases."""
    name: str
    description: str
    test_cases: List[TestCase]
    framework: TestFramework
    language: Language
    base_url: Optional[str] = None
    setup: Optional[List[Dict[str, Any]]] = None
    teardown: Optional[List[Dict[str, Any]]] = None
    config: Dict[str, Any] = field(default_factory=dict)


class NaturalLanguageTestGenerator:
    """
    Generates executable test code from natural language descriptions.
    
    Features:
    - Multi-framework support (pytest, jest, playwright, etc.)
    - Multi-language output (Python, JavaScript, TypeScript, etc.)
    - Intelligent test organization
    - Data-driven testing support
    - Assertion generation
    - Page Object Model generation
    """
    
    def __init__(
        self,
        framework: TestFramework = TestFramework.PYTEST,
        language: Language = Language.PYTHON
    ):
        """
        Initialize test generator.
        
        Args:
            framework: Test framework to generate for
            language: Programming language to generate
        """
        self.framework = framework
        self.language = language
        self.logger = get_logger(__name__)
        
        # Patterns for parsing natural language
        self.action_patterns = {
            'navigate': r'(?:go to|navigate to|open|visit)\s+(.+)',
            'click': r'(?:click|tap|press)\s+(?:on\s+)?(.+)',
            'type': r'(?:type|enter|input|fill)\s+["\']?(.+?)["\']?\s+(?:in|into)\s+(.+)',
            'assert': r'(?:verify|check|assert|ensure)\s+(?:that\s+)?(.+)',
            'wait': r'(?:wait|pause)\s+(?:for\s+)?(\d+)\s*(?:seconds?|ms|milliseconds?)?',
            'screenshot': r'(?:take|capture)\s+(?:a\s+)?screenshot',
            'scroll': r'scroll\s+(?:to|down|up)\s*(.+)?',
            'select': r'select\s+["\']?(.+?)["\']?\s+(?:from|in)\s+(.+)',
            'hover': r'(?:hover|mouse over)\s+(?:on\s+)?(.+)',
            'extract': r'(?:extract|get|save)\s+(.+)',
        }
        
    def parse_natural_language(self, description: str) -> TestCase:
        """
        Parse natural language test description into test case.
        
        Args:
            description: Natural language test description
            
        Returns:
            Parsed test case
        """
        lines = description.strip().split('\n')
        
        # Extract test name (first line or explicit name)
        test_name = self._extract_test_name(lines[0])
        
        # Parse steps and assertions
        steps = []
        assertions = []
        setup = []
        teardown = []
        current_section = 'steps'
        
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
                
            # Check for section markers
            if 'setup:' in line.lower() or 'given:' in line.lower():
                current_section = 'setup'
                continue
            elif 'test:' in line.lower() or 'when:' in line.lower():
                current_section = 'steps'
                continue
            elif 'assert:' in line.lower() or 'then:' in line.lower():
                current_section = 'assertions'
                continue
            elif 'cleanup:' in line.lower() or 'teardown:' in line.lower():
                current_section = 'teardown'
                continue
            
            # Parse the line
            action = self._parse_action(line)
            
            if action:
                if current_section == 'setup':
                    setup.append(action)
                elif current_section == 'steps':
                    steps.append(action)
                elif current_section == 'assertions':
                    assertions.append(action)
                elif current_section == 'teardown':
                    teardown.append(action)
        
        return TestCase(
            name=test_name,
            description=description,
            steps=steps,
            assertions=assertions,
            setup=setup if setup else None,
            teardown=teardown if teardown else None
        )
        
    def _extract_test_name(self, line: str) -> str:
        """Extract test name from line."""
        # Remove common prefixes
        prefixes = ['test:', 'test', 'scenario:', 'feature:']
        line_lower = line.lower()
        for prefix in prefixes:
            if line_lower.startswith(prefix):
                return line[len(prefix):].strip()
        
        # Convert to test name format
        return self._to_test_name(line)
        
    def _to_test_name(self, text: str) -> str:
        """Convert text to valid test name."""
        # Remove special characters and convert to snake_case
        text = re.sub(r'[^\w\s]', '', text)
        text = text.lower().replace(' ', '_')
        if not text.startswith('test_'):
            text = f'test_{text}'
        return text
        
    def _parse_action(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse action from line."""
        line_lower = line.lower()
        
        for action_type, pattern in self.action_patterns.items():
            match = re.search(pattern, line_lower, re.IGNORECASE)
            if match:
                return self._create_action(action_type, match, line)
        
        # Default: treat as comment or assertion
        if any(word in line_lower for word in ['should', 'must', 'expect']):
            return {'type': 'assert', 'text': line}
        
        return {'type': 'comment', 'text': line}
        
    def _create_action(self, action_type: str, match: re.Match, original: str) -> Dict[str, Any]:
        """Create action from regex match."""
        if action_type == 'navigate':
            url = match.group(1).strip()
            # Add protocol if missing
            if not url.startswith('http'):
                url = f'https://{url}'
            return {'type': 'navigate', 'url': url}
            
        elif action_type == 'click':
            target = match.group(1).strip()
            return {'type': 'click', 'target': target}
            
        elif action_type == 'type':
            text = match.group(1).strip()
            target = match.group(2).strip()
            return {'type': 'type', 'text': text, 'target': target}
            
        elif action_type == 'assert':
            condition = match.group(1).strip()
            return {'type': 'assert', 'condition': condition}
            
        elif action_type == 'wait':
            duration = match.group(1)
            unit = match.group(2) if match.lastindex >= 2 else 'seconds'
            return {'type': 'wait', 'duration': duration, 'unit': unit}
            
        elif action_type == 'screenshot':
            return {'type': 'screenshot'}
            
        elif action_type == 'scroll':
            target = match.group(1).strip() if match.lastindex >= 1 else 'bottom'
            return {'type': 'scroll', 'target': target}
            
        elif action_type == 'select':
            option = match.group(1).strip()
            target = match.group(2).strip()
            return {'type': 'select', 'option': option, 'target': target}
            
        elif action_type == 'hover':
            target = match.group(1).strip()
            return {'type': 'hover', 'target': target}
            
        elif action_type == 'extract':
            data = match.group(1).strip()
            return {'type': 'extract', 'data': data}
            
        return {'type': action_type, 'text': original}
        
    def generate_test_suite(self, descriptions: List[str], suite_name: str = "TestSuite") -> TestSuite:
        """
        Generate test suite from multiple descriptions.
        
        Args:
            descriptions: List of natural language test descriptions
            suite_name: Name for the test suite
            
        Returns:
            Complete test suite
        """
        test_cases = []
        
        for desc in descriptions:
            test_case = self.parse_natural_language(desc)
            test_cases.append(test_case)
        
        return TestSuite(
            name=suite_name,
            description=f"Test suite with {len(test_cases)} test cases",
            test_cases=test_cases,
            framework=self.framework,
            language=self.language
        )
        
    def generate_code(self, test_suite: TestSuite) -> str:
        """
        Generate executable test code.
        
        Args:
            test_suite: Test suite to generate code for
            
        Returns:
            Generated test code
        """
        if self.language == Language.PYTHON:
            if self.framework == TestFramework.PYTEST:
                return self._generate_pytest_code(test_suite)
            elif self.framework == TestFramework.UNITTEST:
                return self._generate_unittest_code(test_suite)
            elif self.framework == TestFramework.PLAYWRIGHT:
                return self._generate_playwright_python_code(test_suite)
                
        elif self.language == Language.JAVASCRIPT:
            if self.framework == TestFramework.JEST:
                return self._generate_jest_code(test_suite)
            elif self.framework == TestFramework.MOCHA:
                return self._generate_mocha_code(test_suite)
            elif self.framework == TestFramework.CYPRESS:
                return self._generate_cypress_code(test_suite)
                
        elif self.language == Language.TYPESCRIPT:
            if self.framework == TestFramework.PLAYWRIGHT:
                return self._generate_playwright_typescript_code(test_suite)
                
        raise NotImplementedError(f"Unsupported combination: {self.language}/{self.framework}")
        
    def _generate_pytest_code(self, test_suite: TestSuite) -> str:
        """Generate pytest code."""
        code = [
            '"""',
            f'{test_suite.description}',
            f'Generated by WebPilot Natural Language Test Generator',
            '"""',
            '',
            'import pytest',
            'from webpilot import WebPilot',
            '',
        ]
        
        # Add fixtures if needed
        if test_suite.setup or any(tc.setup for tc in test_suite.test_cases):
            code.extend([
                '@pytest.fixture',
                'def pilot():',
                '    """WebPilot fixture."""',
                '    pilot = WebPilot(headless=True)',
                '    yield pilot',
                '    pilot.close()',
                '',
            ])
        
        # Generate test class
        code.extend([
            f'class {test_suite.name}:',
            f'    """Test suite: {test_suite.name}"""',
            '',
        ])
        
        # Generate each test case
        for test_case in test_suite.test_cases:
            code.extend(self._generate_pytest_test_method(test_case))
            code.append('')
        
        return '\n'.join(code)
        
    def _generate_pytest_test_method(self, test_case: TestCase) -> List[str]:
        """Generate pytest test method."""
        code = [
            f'    def {test_case.name}(self, pilot):',
            f'        """',
            f'        {test_case.description}',
            f'        """',
        ]
        
        # Setup
        if test_case.setup:
            code.append('        # Setup')
            for action in test_case.setup:
                code.append(f'        {self._action_to_python(action)}')
            code.append('')
        
        # Test steps
        code.append('        # Test steps')
        for action in test_case.steps:
            code.append(f'        {self._action_to_python(action)}')
        
        # Assertions
        if test_case.assertions:
            code.append('')
            code.append('        # Assertions')
            for assertion in test_case.assertions:
                code.append(f'        {self._assertion_to_python(assertion)}')
        
        # Teardown
        if test_case.teardown:
            code.append('')
            code.append('        # Teardown')
            for action in test_case.teardown:
                code.append(f'        {self._action_to_python(action)}')
        
        return code
        
    def _action_to_python(self, action: Dict[str, Any]) -> str:
        """Convert action to Python code."""
        action_type = action.get('type')
        
        if action_type == 'navigate':
            return f'pilot.navigate("{action["url"]}")'
            
        elif action_type == 'click':
            target = action['target']
            if '"' in target:
                return f"pilot.click(text='{target}')"
            else:
                return f'pilot.click(text="{target}")'
                
        elif action_type == 'type':
            text = action['text']
            target = action['target']
            return f'pilot.type_text("{text}", selector="{target}")'
            
        elif action_type == 'wait':
            duration = action['duration']
            return f'pilot.wait({duration})'
            
        elif action_type == 'screenshot':
            return 'pilot.screenshot()'
            
        elif action_type == 'scroll':
            target = action.get('target', 'bottom')
            return f'pilot.scroll_to("{target}")'
            
        elif action_type == 'select':
            option = action['option']
            target = action['target']
            return f'pilot.select_option("{option}", selector="{target}")'
            
        elif action_type == 'hover':
            target = action['target']
            return f'pilot.hover(text="{target}")'
            
        elif action_type == 'extract':
            data = action['data']
            return f'data = pilot.extract_page_content()  # Extract: {data}'
            
        elif action_type == 'comment':
            return f'# {action["text"]}'
            
        return f'# TODO: {action}'
        
    def _assertion_to_python(self, assertion: Dict[str, Any]) -> str:
        """Convert assertion to Python code."""
        if assertion.get('type') == 'assert':
            condition = assertion.get('condition', assertion.get('text', ''))
            
            # Common assertion patterns
            if 'contains' in condition:
                parts = condition.split('contains')
                if len(parts) == 2:
                    target = parts[0].strip()
                    expected = parts[1].strip().strip('"\'')
                    return f'assert "{expected}" in pilot.get_page_source()'
                    
            elif 'visible' in condition:
                element = condition.replace('is visible', '').strip()
                return f'assert pilot.is_element_visible("{element}")'
                
            elif 'exists' in condition:
                element = condition.replace('exists', '').strip()
                return f'assert pilot.find_element("{element}") is not None'
                
            elif 'equals' in condition or '=' in condition:
                parts = re.split(r'equals|=', condition)
                if len(parts) == 2:
                    actual = parts[0].strip()
                    expected = parts[1].strip().strip('"\'')
                    return f'assert {actual} == "{expected}"'
            
            # Default
            return f'# TODO: Assert {condition}'
            
        return f'# Assertion: {assertion}'
        
    def _generate_unittest_code(self, test_suite: TestSuite) -> str:
        """Generate unittest code."""
        code = [
            '"""',
            f'{test_suite.description}',
            '"""',
            '',
            'import unittest',
            'from webpilot import WebPilot',
            '',
            f'class {test_suite.name}(unittest.TestCase):',
            '    """Test suite"""',
            '',
            '    def setUp(self):',
            '        self.pilot = WebPilot(headless=True)',
            '',
            '    def tearDown(self):',
            '        self.pilot.close()',
            '',
        ]
        
        for test_case in test_suite.test_cases:
            code.extend(self._generate_unittest_test_method(test_case))
            code.append('')
        
        code.extend([
            'if __name__ == "__main__":',
            '    unittest.main()',
        ])
        
        return '\n'.join(code)
        
    def _generate_unittest_test_method(self, test_case: TestCase) -> List[str]:
        """Generate unittest test method."""
        code = [
            f'    def {test_case.name}(self):',
            f'        """Test: {test_case.description}"""',
        ]
        
        for action in test_case.steps:
            code.append(f'        {self._action_to_python(action)}')
        
        for assertion in test_case.assertions:
            code.append(f'        {self._assertion_to_python(assertion).replace("assert ", "self.assertTrue(")})')
        
        return code
        
    def _generate_jest_code(self, test_suite: TestSuite) -> str:
        """Generate Jest code."""
        code = [
            '/**',
            f' * {test_suite.description}',
            ' * Generated by WebPilot',
            ' */',
            '',
            "const { WebPilot } = require('webpilot');",
            '',
            f"describe('{test_suite.name}', () => {{",
            '  let pilot;',
            '',
            '  beforeAll(async () => {',
            '    pilot = new WebPilot({ headless: true });',
            '  });',
            '',
            '  afterAll(async () => {',
            '    await pilot.close();',
            '  });',
            '',
        ]
        
        for test_case in test_suite.test_cases:
            code.extend(self._generate_jest_test(test_case))
            code.append('')
        
        code.append('});')
        
        return '\n'.join(code)
        
    def _generate_jest_test(self, test_case: TestCase) -> List[str]:
        """Generate Jest test."""
        code = [
            f"  test('{test_case.description}', async () => {{",
        ]
        
        for action in test_case.steps:
            code.append(f'    {self._action_to_javascript(action)}')
        
        for assertion in test_case.assertions:
            code.append(f'    {self._assertion_to_javascript(assertion)}')
        
        code.append('  });')
        
        return code
        
    def _action_to_javascript(self, action: Dict[str, Any]) -> str:
        """Convert action to JavaScript code."""
        action_type = action.get('type')
        
        if action_type == 'navigate':
            return f'await pilot.navigate("{action["url"]}");'
        elif action_type == 'click':
            return f'await pilot.click("{action["target"]}");'
        elif action_type == 'type':
            return f'await pilot.type("{action["text"]}", "{action["target"]}");'
        elif action_type == 'wait':
            return f'await pilot.wait({action["duration"]});'
        elif action_type == 'screenshot':
            return 'await pilot.screenshot();'
        
        return f'// TODO: {action}'
        
    def _assertion_to_javascript(self, assertion: Dict[str, Any]) -> str:
        """Convert assertion to JavaScript code."""
        condition = assertion.get('condition', assertion.get('text', ''))
        
        if 'contains' in condition:
            parts = condition.split('contains')
            if len(parts) == 2:
                expected = parts[1].strip().strip('"\'')
                return f'expect(await pilot.getPageContent()).toContain("{expected}");'
        
        return f'// TODO: Assert {condition}'
        
    def _generate_playwright_python_code(self, test_suite: TestSuite) -> str:
        """Generate Playwright Python code."""
        code = [
            '"""Playwright tests generated by WebPilot"""',
            '',
            'import pytest',
            'from playwright.sync_api import Page, expect',
            '',
        ]
        
        for test_case in test_suite.test_cases:
            code.extend([
                f'def {test_case.name}(page: Page):',
                f'    """Test: {test_case.description}"""',
            ])
            
            for action in test_case.steps:
                code.append(f'    {self._action_to_playwright_python(action)}')
            
            for assertion in test_case.assertions:
                code.append(f'    {self._assertion_to_playwright_python(assertion)}')
            
            code.append('')
        
        return '\n'.join(code)
        
    def _action_to_playwright_python(self, action: Dict[str, Any]) -> str:
        """Convert action to Playwright Python code."""
        action_type = action.get('type')
        
        if action_type == 'navigate':
            return f'page.goto("{action["url"]}")'
        elif action_type == 'click':
            return f'page.click("text={action["target"]}")'
        elif action_type == 'type':
            return f'page.fill("{action["target"]}", "{action["text"]}")'
        elif action_type == 'wait':
            return f'page.wait_for_timeout({int(action["duration"]) * 1000})'
        elif action_type == 'screenshot':
            return 'page.screenshot()'
        
        return f'# TODO: {action}'
        
    def _assertion_to_playwright_python(self, assertion: Dict[str, Any]) -> str:
        """Convert assertion to Playwright Python code."""
        condition = assertion.get('condition', assertion.get('text', ''))
        
        if 'visible' in condition:
            element = condition.replace('is visible', '').strip()
            return f'expect(page.locator("text={element}")).to_be_visible()'
        elif 'contains' in condition:
            parts = condition.split('contains')
            if len(parts) == 2:
                expected = parts[1].strip().strip('"\'')
                return f'expect(page).to_have_text("{expected}")'
        
        return f'# TODO: Assert {condition}'
        
    def _generate_cypress_code(self, test_suite: TestSuite) -> str:
        """Generate Cypress code."""
        code = [
            '/**',
            f' * Cypress tests for {test_suite.name}',
            ' */',
            '',
            f"describe('{test_suite.name}', () => {{",
        ]
        
        for test_case in test_suite.test_cases:
            code.extend([
                f"  it('{test_case.description}', () => {{",
            ])
            
            for action in test_case.steps:
                code.append(f'    {self._action_to_cypress(action)}')
            
            for assertion in test_case.assertions:
                code.append(f'    {self._assertion_to_cypress(assertion)}')
            
            code.extend([
                '  });',
                '',
            ])
        
        code.append('});')
        
        return '\n'.join(code)
        
    def _action_to_cypress(self, action: Dict[str, Any]) -> str:
        """Convert action to Cypress code."""
        action_type = action.get('type')
        
        if action_type == 'navigate':
            return f'cy.visit("{action["url"]}");'
        elif action_type == 'click':
            return f'cy.contains("{action["target"]}").click();'
        elif action_type == 'type':
            return f'cy.get("{action["target"]}").type("{action["text"]}");'
        elif action_type == 'wait':
            return f'cy.wait({int(action["duration"]) * 1000});'
        elif action_type == 'screenshot':
            return 'cy.screenshot();'
        
        return f'// TODO: {action}'
        
    def _assertion_to_cypress(self, assertion: Dict[str, Any]) -> str:
        """Convert assertion to Cypress code."""
        condition = assertion.get('condition', assertion.get('text', ''))
        
        if 'visible' in condition:
            element = condition.replace('is visible', '').strip()
            return f'cy.contains("{element}").should("be.visible");'
        elif 'contains' in condition:
            parts = condition.split('contains')
            if len(parts) == 2:
                expected = parts[1].strip().strip('"\'')
                return f'cy.contains("{expected}").should("exist");'
        
        return f'// TODO: Assert {condition}'
        
    def _generate_playwright_typescript_code(self, test_suite: TestSuite) -> str:
        """Generate Playwright TypeScript code."""
        code = [
            '/**',
            f' * Playwright TypeScript tests for {test_suite.name}',
            ' */',
            '',
            "import { test, expect } from '@playwright/test';",
            '',
        ]
        
        for test_case in test_suite.test_cases:
            code.extend([
                f"test('{test_case.description}', async ({{ page }}) => {{",
            ])
            
            for action in test_case.steps:
                code.append(f'  {self._action_to_playwright_typescript(action)}')
            
            for assertion in test_case.assertions:
                code.append(f'  {self._assertion_to_playwright_typescript(assertion)}')
            
            code.extend([
                '});',
                '',
            ])
        
        return '\n'.join(code)
        
    def _action_to_playwright_typescript(self, action: Dict[str, Any]) -> str:
        """Convert action to Playwright TypeScript code."""
        action_type = action.get('type')
        
        if action_type == 'navigate':
            return f'await page.goto("{action["url"]}");'
        elif action_type == 'click':
            return f'await page.click("text={action["target"]}");'
        elif action_type == 'type':
            return f'await page.fill("{action["target"]}", "{action["text"]}");'
        elif action_type == 'wait':
            return f'await page.waitForTimeout({int(action["duration"]) * 1000});'
        elif action_type == 'screenshot':
            return 'await page.screenshot();'
        
        return f'// TODO: {action}'
        
    def _assertion_to_playwright_typescript(self, assertion: Dict[str, Any]) -> str:
        """Convert assertion to Playwright TypeScript code."""
        condition = assertion.get('condition', assertion.get('text', ''))
        
        if 'visible' in condition:
            element = condition.replace('is visible', '').strip()
            return f'await expect(page.locator("text={element}")).toBeVisible();'
        elif 'contains' in condition:
            parts = condition.split('contains')
            if len(parts) == 2:
                expected = parts[1].strip().strip('"\'')
                return f'await expect(page).toHaveText("{expected}");'
        
        return f'// TODO: Assert {condition}'
        
    def export_to_file(self, test_suite: TestSuite, output_path: str):
        """
        Export test suite to file.
        
        Args:
            test_suite: Test suite to export
            output_path: Output file path
        """
        code = self.generate_code(test_suite)
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(code)
        
        self.logger.info(f"Exported test suite to {output_path}")
        
    def generate_page_object(self, test_cases: List[TestCase]) -> str:
        """
        Generate Page Object Model from test cases.
        
        Args:
            test_cases: List of test cases
            
        Returns:
            Page Object code
        """
        # Extract unique elements from all test cases
        elements = set()
        
        for test_case in test_cases:
            for action in test_case.steps + test_case.assertions:
                if 'target' in action:
                    elements.add(action['target'])
        
        # Generate Page Object class
        if self.language == Language.PYTHON:
            return self._generate_python_page_object(elements)
        elif self.language == Language.JAVASCRIPT:
            return self._generate_javascript_page_object(elements)
        
        return ""
        
    def _generate_python_page_object(self, elements: set) -> str:
        """Generate Python Page Object."""
        code = [
            '"""Page Object Model generated by WebPilot"""',
            '',
            'class PageObject:',
            '    """Page Object for test automation."""',
            '',
            '    def __init__(self, pilot):',
            '        self.pilot = pilot',
            '',
            '    # Element locators',
        ]
        
        for element in sorted(elements):
            # Convert to valid Python attribute name
            attr_name = re.sub(r'[^\w]', '_', element.lower())
            code.append(f'    {attr_name} = "{element}"')
        
        code.extend([
            '',
            '    # Page methods',
            '    def navigate_to(self, url):',
            '        """Navigate to URL."""',
            '        return self.pilot.navigate(url)',
            '',
            '    def click_element(self, element):',
            '        """Click an element."""',
            '        return self.pilot.click(selector=element)',
            '',
            '    def enter_text(self, element, text):',
            '        """Enter text in element."""',
            '        return self.pilot.type_text(text, selector=element)',
        ])
        
        return '\n'.join(code)
        
    def _generate_javascript_page_object(self, elements: set) -> str:
        """Generate JavaScript Page Object."""
        code = [
            '/**',
            ' * Page Object Model generated by WebPilot',
            ' */',
            '',
            'class PageObject {',
            '  constructor(pilot) {',
            '    this.pilot = pilot;',
            '',
            '    // Element locators',
        ]
        
        for element in sorted(elements):
            # Convert to valid JavaScript property name
            prop_name = re.sub(r'[^\w]', '_', element.lower())
            code.append(f'    this.{prop_name} = "{element}";')
        
        code.extend([
            '  }',
            '',
            '  // Page methods',
            '  async navigateTo(url) {',
            '    return await this.pilot.navigate(url);',
            '  }',
            '',
            '  async clickElement(element) {',
            '    return await this.pilot.click(element);',
            '  }',
            '',
            '  async enterText(element, text) {',
            '    return await this.pilot.typeText(text, element);',
            '  }',
            '}',
            '',
            'module.exports = PageObject;',
        ])
        
        return '\n'.join(code)


class SmartTestRecorder:
    """
    Records user interactions and generates tests from them.
    
    Features:
    - Record browser sessions
    - Learn patterns from interactions
    - Generate optimized test code
    - Suggest improvements
    """
    
    def __init__(self, pilot: Optional[WebPilot] = None):
        """Initialize test recorder."""
        self.pilot = pilot or WebPilot()
        self.recording = []
        self.is_recording = False
        
    def start_recording(self):
        """Start recording user interactions."""
        self.is_recording = True
        self.recording = []
        self.logger.info("Started recording interactions")
        
    def stop_recording(self) -> List[Dict[str, Any]]:
        """Stop recording and return interactions."""
        self.is_recording = False
        self.logger.info(f"Stopped recording. Captured {len(self.recording)} interactions")
        return self.recording
        
    def record_action(self, action_type: str, **kwargs):
        """Record a single action."""
        if self.is_recording:
            self.recording.append({
                'type': action_type,
                'timestamp': time.time(),
                **kwargs
            })
            
    def generate_test_from_recording(
        self,
        name: str = "recorded_test",
        framework: TestFramework = TestFramework.PYTEST
    ) -> str:
        """
        Generate test code from recorded interactions.
        
        Args:
            name: Test name
            framework: Test framework
            
        Returns:
            Generated test code
        """
        generator = NaturalLanguageTestGenerator(framework=framework)
        
        # Convert recording to test case
        steps = []
        for action in self.recording:
            if action['type'] == 'navigate':
                steps.append({'type': 'navigate', 'url': action['url']})
            elif action['type'] == 'click':
                steps.append({'type': 'click', 'target': action.get('selector', action.get('text'))})
            elif action['type'] == 'type':
                steps.append({'type': 'type', 'text': action['text'], 'target': action.get('selector', '')})
            elif action['type'] == 'screenshot':
                steps.append({'type': 'screenshot'})
        
        test_case = TestCase(
            name=name,
            description=f"Recorded test with {len(steps)} steps",
            steps=steps,
            assertions=[]
        )
        
        test_suite = TestSuite(
            name="RecordedTests",
            description="Tests generated from recordings",
            test_cases=[test_case],
            framework=framework,
            language=Language.PYTHON
        )
        
        return generator.generate_code(test_suite)
        
    def learn_patterns(self) -> Dict[str, Any]:
        """
        Learn patterns from recorded interactions.
        
        Returns:
            Learned patterns and suggestions
        """
        patterns = {
            'common_flows': [],
            'repeated_actions': [],
            'wait_times': [],
            'error_recoveries': []
        }
        
        # Analyze recording for patterns
        action_counts = {}
        for action in self.recording:
            action_type = action['type']
            action_counts[action_type] = action_counts.get(action_type, 0) + 1
        
        patterns['action_frequency'] = action_counts
        
        # Find repeated sequences
        sequences = self._find_repeated_sequences()
        patterns['common_flows'] = sequences
        
        return patterns
        
    def _find_repeated_sequences(self, min_length: int = 3) -> List[List[Dict]]:
        """Find repeated action sequences."""
        sequences = []
        
        # Simple pattern matching (can be enhanced with more sophisticated algorithms)
        for i in range(len(self.recording) - min_length):
            sequence = self.recording[i:i + min_length]
            
            # Check if this sequence appears again
            for j in range(i + min_length, len(self.recording) - min_length):
                if self._sequences_match(sequence, self.recording[j:j + min_length]):
                    sequences.append(sequence)
                    break
        
        return sequences
        
    def _sequences_match(self, seq1: List[Dict], seq2: List[Dict]) -> bool:
        """Check if two sequences match."""
        if len(seq1) != len(seq2):
            return False
        
        for a1, a2 in zip(seq1, seq2):
            if a1['type'] != a2['type']:
                return False
        
        return True


# Example usage and demonstration
if __name__ == "__main__":
    # Example 1: Generate test from natural language
    generator = NaturalLanguageTestGenerator(
        framework=TestFramework.PYTEST,
        language=Language.PYTHON
    )
    
    test_description = """
    Test: User login flow
    
    Setup:
    - Go to https://example.com
    
    Test:
    - Click on "Login" button
    - Type "user@example.com" in email field
    - Type "password123" in password field
    - Click "Submit"
    - Wait for 2 seconds
    
    Assert:
    - Verify that dashboard is visible
    - Verify that welcome message contains "Hello"
    """
    
    test_case = generator.parse_natural_language(test_description)
    test_suite = TestSuite(
        name="LoginTests",
        description="User login test suite",
        test_cases=[test_case],
        framework=TestFramework.PYTEST,
        language=Language.PYTHON
    )
    
    code = generator.generate_code(test_suite)
    print("Generated pytest code:")
    print(code)
    
    # Example 2: Generate multiple framework outputs
    frameworks = [
        (TestFramework.JEST, Language.JAVASCRIPT),
        (TestFramework.PLAYWRIGHT, Language.PYTHON),
        (TestFramework.CYPRESS, Language.JAVASCRIPT)
    ]
    
    for framework, language in frameworks:
        gen = NaturalLanguageTestGenerator(framework=framework, language=language)
        suite = TestSuite(
            name="MultiFrameworkTests",
            description="Same test in multiple frameworks",
            test_cases=[test_case],
            framework=framework,
            language=language
        )
        print(f"\n\nGenerated {framework.value} code:")
        print(gen.generate_code(suite)[:500])  # First 500 chars