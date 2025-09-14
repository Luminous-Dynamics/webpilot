#!/usr/bin/env python
"""
Integration tests for all new WebPilot v1.4.0 features.

Tests:
1. Universal CLI
2. Visual Intelligence
3. Autonomous Agent
4. Natural Language Test Generation
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Import all new features
from webpilot.cli.universal_cli import (
    execute_direct_command,
    execute_with_openai,
    execute_with_ollama,
    execute_with_langchain
)
from webpilot.intelligence.visual_intelligence import (
    VisualIntelligence,
    VisualWebPilot,
    VisualElement,
    VisualAnalysis
)
from webpilot.intelligence.autonomous_agent import (
    AutonomousAgent,
    TaskPlan,
    TaskStep,
    TaskStatus,
    RecoveryStrategy,
    SmartAutomation
)
from webpilot.testing.natural_language_tests import (
    NaturalLanguageTestGenerator,
    TestFramework,
    Language,
    TestCase,
    TestSuite,
    SmartTestRecorder
)


class TestUniversalCLI:
    """Test Universal CLI functionality."""
    
    @patch('webpilot.cli.universal_cli.WebPilot')
    def test_execute_direct_command_navigate(self, mock_webpilot):
        """Test direct command execution for navigation."""
        mock_pilot = Mock()
        mock_pilot.start.return_value = Mock(success=True, data="navigated", error=None)
        mock_webpilot.return_value = mock_pilot
        
        result = execute_direct_command("navigate to https://example.com", headless=True)
        
        assert result['success'] is True
        mock_pilot.start.assert_called_once_with("https://example.com")
    
    @patch('webpilot.cli.universal_cli.WebPilot')
    def test_execute_direct_command_screenshot(self, mock_webpilot):
        """Test direct command execution for screenshot."""
        mock_pilot = Mock()
        mock_pilot.screenshot.return_value = Mock(success=True, data="screenshot.png", error=None)
        mock_webpilot.return_value = mock_pilot
        
        result = execute_direct_command("take a screenshot", headless=True)
        
        assert result['success'] is True
        mock_pilot.screenshot.assert_called_once()
    
    @patch('webpilot.cli.universal_cli.OpenAI')
    @patch('webpilot.cli.universal_cli.OpenAIAdapter')
    def test_execute_with_openai(self, mock_adapter_class, mock_openai_class):
        """Test OpenAI integration."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(function_call=Mock(
            name="navigate",
            arguments='{"url": "https://example.com"}'
        )))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        # Mock adapter
        mock_adapter = Mock()
        mock_adapter.get_functions.return_value = []
        mock_adapter.execute_function.return_value = asyncio.coroutine(
            lambda: {"success": True, "data": "executed"}
        )()
        mock_adapter_class.return_value = mock_adapter
        
        result = execute_with_openai("Go to example.com", "gpt-4", "test-key", True)
        
        # Verify OpenAI was called
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('requests.post')
    def test_execute_with_ollama(self, mock_post):
        """Test Ollama integration."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "navigate to https://example.com"}
        mock_post.return_value = mock_response
        
        with patch('webpilot.cli.universal_cli.execute_direct_command') as mock_exec:
            mock_exec.return_value = {"success": True}
            
            result = execute_with_ollama(
                "Go to example.com",
                "llama2",
                "http://localhost:11434",
                True
            )
            
            assert result['success'] is True
            mock_post.assert_called_once()


class TestVisualIntelligence:
    """Test Visual Intelligence features."""
    
    @patch('webpilot.intelligence.visual_intelligence.WebPilot')
    def test_visual_intelligence_init(self, mock_webpilot):
        """Test VisualIntelligence initialization."""
        vi = VisualIntelligence()
        assert vi.pilot is not None
        assert vi.current_screenshot is None
        assert vi.current_analysis is None
    
    @patch('PIL.Image.open')
    @patch('webpilot.intelligence.visual_intelligence.WebPilot')
    def test_capture_and_analyze(self, mock_webpilot, mock_image_open):
        """Test screenshot capture and analysis."""
        # Mock pilot
        mock_pilot = Mock()
        mock_pilot.screenshot.return_value = Mock(
            success=True,
            data="/tmp/screenshot.png",
            error=None
        )
        
        # Mock image
        mock_image = Mock()
        mock_image.size = (1920, 1080)
        mock_image_open.return_value = mock_image
        
        vi = VisualIntelligence(mock_pilot)
        analysis = vi.capture_and_analyze()
        
        assert isinstance(analysis, VisualAnalysis)
        assert vi.current_screenshot == "/tmp/screenshot.png"
        mock_pilot.screenshot.assert_called_once()
    
    def test_visual_element_creation(self):
        """Test VisualElement dataclass."""
        element = VisualElement(
            type="button",
            text="Click Me",
            location=(100, 200),
            size=(80, 30),
            confidence=0.95,
            attributes={"class": "primary-button"}
        )
        
        assert element.type == "button"
        assert element.text == "Click Me"
        assert element.location == (100, 200)
        assert element.confidence == 0.95
    
    @patch('webpilot.intelligence.visual_intelligence.WebPilot')
    def test_click_by_description(self, mock_webpilot):
        """Test clicking element by description."""
        mock_pilot = Mock()
        mock_pilot.click.return_value = Mock(success=True)
        
        vi = VisualIntelligence(mock_pilot)
        
        # Create mock analysis
        vi.current_analysis = VisualAnalysis(
            elements=[
                VisualElement(
                    type="button",
                    text="Submit",
                    location=(100, 200),
                    size=(80, 30),
                    confidence=0.95,
                    attributes={}
                )
            ],
            layout="standard",
            primary_content="form",
            navigation=[],
            forms=[],
            images=[],
            overall_description="Page with submit button"
        )
        
        result = vi.click_by_description("submit button")
        
        assert result.success is True
        mock_pilot.click.assert_called_once_with(x=140, y=215)  # Center of button
    
    def test_export_for_llm(self):
        """Test exporting visual analysis for LLM consumption."""
        vi = VisualIntelligence()
        
        vi.current_analysis = VisualAnalysis(
            elements=[
                VisualElement(
                    type="button",
                    text="Login",
                    location=(100, 100),
                    size=(100, 40),
                    confidence=0.9,
                    attributes={}
                )
            ],
            layout="header, main content, footer",
            primary_content="Login form",
            navigation=["Home", "About", "Contact"],
            forms=[{"fields": [], "buttons": []}],
            images=[],
            overall_description="Login page"
        )
        
        export = vi.export_for_llm()
        
        assert "description" in export
        assert "layout" in export
        assert "navigation" in export
        assert len(export["clickable_elements"]) > 0


class TestAutonomousAgent:
    """Test Autonomous Agent functionality."""
    
    @patch('webpilot.intelligence.autonomous_agent.WebPilot')
    def test_autonomous_agent_init(self, mock_webpilot):
        """Test AutonomousAgent initialization."""
        agent = AutonomousAgent()
        
        assert agent.max_recovery_attempts == 3
        assert agent.enable_visual_fallback is True
        assert agent.enable_learning is True
        assert len(agent.success_patterns) == 0
    
    def test_create_plan(self):
        """Test task plan creation."""
        agent = AutonomousAgent()
        
        plan = agent.create_plan("login to website")
        
        assert isinstance(plan, TaskPlan)
        assert plan.goal == "login to website"
        assert len(plan.steps) > 0
        assert plan.steps[0].action == "find_element"
    
    def test_task_step_creation(self):
        """Test TaskStep dataclass."""
        step = TaskStep(
            action="click",
            arguments={"selector": "#submit"},
            description="Click submit button",
            status=TaskStatus.PENDING
        )
        
        assert step.action == "click"
        assert step.status == TaskStatus.PENDING
        assert step.recovery_attempts == 0
    
    @pytest.mark.asyncio
    async def test_execute_plan(self):
        """Test plan execution."""
        agent = AutonomousAgent()
        
        # Create simple plan
        plan = TaskPlan(
            goal="test navigation",
            steps=[
                TaskStep(
                    action="navigate",
                    arguments={"url": "https://example.com"},
                    description="Go to example.com"
                )
            ]
        )
        
        # Mock execute_action
        with patch.object(agent, '_execute_action') as mock_exec:
            mock_exec.return_value = asyncio.coroutine(
                lambda: Mock(success=True, data="navigated", error=None)
            )()
            
            completed_plan = await agent.execute_plan(plan)
            
            assert completed_plan.success_rate > 0
            assert plan.steps[0].status == TaskStatus.COMPLETED
    
    def test_determine_recovery_strategy(self):
        """Test recovery strategy determination."""
        agent = AutonomousAgent()
        
        step = TaskStep(
            action="click",
            arguments={"selector": "#button"},
            description="Click button"
        )
        
        # Test "not found" error
        result = Mock(error="Element not found")
        strategy = agent._determine_recovery_strategy(step, result)
        assert strategy == RecoveryStrategy.VISUAL_FALLBACK
        
        # Test timeout error
        result = Mock(error="Timeout waiting for element")
        strategy = agent._determine_recovery_strategy(step, result)
        assert strategy == RecoveryStrategy.WAIT_RETRY
        
        # Test stale element
        result = Mock(error="Stale element reference")
        strategy = agent._determine_recovery_strategy(step, result)
        assert strategy == RecoveryStrategy.REFRESH_RETRY
    
    def test_learning_from_execution(self):
        """Test learning from plan execution."""
        agent = AutonomousAgent()
        
        plan = TaskPlan(
            goal="test",
            steps=[
                TaskStep(
                    action="click",
                    arguments={"selector": "#btn"},
                    description="Click",
                    status=TaskStatus.COMPLETED,
                    result=Mock(success=True)
                ),
                TaskStep(
                    action="type",
                    arguments={"text": "test"},
                    description="Type",
                    status=TaskStatus.FAILED,
                    error="Element not found"
                )
            ]
        )
        
        agent._learn_from_execution(plan)
        
        assert "click" in agent.success_patterns
        assert "type" in agent.failure_patterns
        assert len(agent.success_patterns["click"]) == 1
        assert len(agent.failure_patterns["type"]) == 1


class TestNaturalLanguageTests:
    """Test Natural Language Test Generation."""
    
    def test_generator_init(self):
        """Test NaturalLanguageTestGenerator initialization."""
        generator = NaturalLanguageTestGenerator(
            framework=TestFramework.PYTEST,
            language=Language.PYTHON
        )
        
        assert generator.framework == TestFramework.PYTEST
        assert generator.language == Language.PYTHON
        assert len(generator.action_patterns) > 0
    
    def test_parse_natural_language(self):
        """Test parsing natural language to test case."""
        generator = NaturalLanguageTestGenerator()
        
        description = """
        Test: User login
        1. Go to login page
        2. Enter "user@example.com" in email field
        3. Enter "password123" in password field
        4. Click login button
        Verify that dashboard is displayed
        """
        
        test_case = generator.parse_natural_language(description)
        
        assert isinstance(test_case, TestCase)
        assert test_case.name == "test_user_login"
        assert len(test_case.steps) > 0
        assert test_case.steps[0]['type'] == 'navigate'
        assert len(test_case.assertions) > 0
    
    def test_generate_pytest_code(self):
        """Test pytest code generation."""
        generator = NaturalLanguageTestGenerator(
            framework=TestFramework.PYTEST,
            language=Language.PYTHON
        )
        
        test_case = TestCase(
            name="test_search",
            description="Test search functionality",
            steps=[
                {"type": "navigate", "url": "https://example.com"},
                {"type": "type", "text": "python", "target": "#search"},
                {"type": "click", "target": "Search"}
            ],
            assertions=[
                {"type": "assert", "condition": "results contains Python"}
            ]
        )
        
        test_suite = TestSuite(
            name="SearchTests",
            description="Search test suite",
            test_cases=[test_case],
            framework=TestFramework.PYTEST,
            language=Language.PYTHON
        )
        
        code = generator.generate_code(test_suite)
        
        assert "import pytest" in code
        assert "from webpilot import WebPilot" in code
        assert "def test_search" in code
        assert 'pilot.navigate("https://example.com")' in code
    
    def test_generate_jest_code(self):
        """Test Jest code generation."""
        generator = NaturalLanguageTestGenerator(
            framework=TestFramework.JEST,
            language=Language.JAVASCRIPT
        )
        
        test_case = TestCase(
            name="test_navigation",
            description="Test navigation",
            steps=[
                {"type": "navigate", "url": "https://example.com"}
            ],
            assertions=[]
        )
        
        test_suite = TestSuite(
            name="NavTests",
            description="Navigation tests",
            test_cases=[test_case],
            framework=TestFramework.JEST,
            language=Language.JAVASCRIPT
        )
        
        code = generator.generate_code(test_suite)
        
        assert "describe(" in code
        assert "test(" in code
        assert "await pilot.navigate" in code
    
    def test_generate_page_object(self):
        """Test Page Object Model generation."""
        generator = NaturalLanguageTestGenerator()
        
        test_cases = [
            TestCase(
                name="test1",
                description="Test 1",
                steps=[
                    {"type": "click", "target": "#submit-button"},
                    {"type": "type", "text": "test", "target": "#email-field"}
                ],
                assertions=[]
            )
        ]
        
        page_object = generator.generate_page_object(test_cases)
        
        assert "class PageObject:" in page_object
        assert "submit_button" in page_object
        assert "email_field" in page_object
        assert "def navigate_to" in page_object
    
    def test_smart_test_recorder(self):
        """Test SmartTestRecorder functionality."""
        recorder = SmartTestRecorder()
        
        # Start recording
        recorder.start_recording()
        assert recorder.is_recording is True
        
        # Record actions
        recorder.record_action("navigate", url="https://example.com")
        recorder.record_action("click", text="Login")
        recorder.record_action("type", text="user@example.com", selector="#email")
        
        # Stop recording
        recording = recorder.stop_recording()
        assert len(recording) == 3
        assert recording[0]['type'] == 'navigate'
        
        # Generate test from recording
        test_code = recorder.generate_test_from_recording(
            name="test_recorded_flow",
            framework=TestFramework.PYTEST
        )
        
        assert "def test_recorded_flow" in test_code
        assert "pilot.navigate" in test_code


class TestIntegration:
    """Test integration between all features."""
    
    @pytest.mark.asyncio
    async def test_visual_autonomous_integration(self):
        """Test Visual Intelligence with Autonomous Agent."""
        # Create visual-enabled autonomous agent
        agent = AutonomousAgent(enable_visual_fallback=True)
        
        # Create plan that requires visual fallback
        plan = TaskPlan(
            goal="click button visually",
            steps=[
                TaskStep(
                    action="visual_click",
                    arguments={"description": "submit button"},
                    description="Click submit using visual recognition"
                )
            ]
        )
        
        # Mock the visual click
        with patch.object(agent, '_execute_action') as mock_exec:
            mock_exec.return_value = asyncio.coroutine(
                lambda: Mock(success=True, data="clicked")
            )()
            
            completed_plan = await agent.execute_plan(plan)
            assert completed_plan.success_rate > 0
    
    def test_cli_with_test_generation(self):
        """Test CLI generating natural language tests."""
        # Simulate CLI command that generates tests
        test_description = "Test: Click login button and verify dashboard"
        
        generator = NaturalLanguageTestGenerator()
        test_case = generator.parse_natural_language(test_description)
        
        assert test_case.name == "test_click_login_button_and_verify_dashboard"
        assert len(test_case.steps) > 0
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete workflow from NL to execution."""
        # 1. Natural language description
        description = """
        Test: Search for Python
        1. Go to google.com
        2. Type "Python programming" in search box
        3. Click search button
        Verify results contain Python
        """
        
        # 2. Generate test case
        generator = NaturalLanguageTestGenerator()
        test_case = generator.parse_natural_language(description)
        
        # 3. Create autonomous agent
        agent = AutonomousAgent()
        
        # 4. Convert test case to plan
        plan = TaskPlan(
            goal=test_case.description,
            steps=[
                TaskStep(
                    action=step['type'],
                    arguments=step,
                    description=f"Step: {step['type']}"
                )
                for step in test_case.steps
            ]
        )
        
        # 5. Mock execution
        with patch.object(agent, '_execute_action') as mock_exec:
            mock_exec.return_value = asyncio.coroutine(
                lambda: Mock(success=True)
            )()
            
            completed_plan = await agent.execute_plan(plan)
            
            assert completed_plan.success_rate > 0
            assert all(s.status == TaskStatus.COMPLETED for s in plan.steps)


# Test runners
def test_all_features():
    """Quick test that all features are importable and basic functionality works."""
    # CLI
    from webpilot.cli.universal_cli import cli
    assert cli is not None
    
    # Visual Intelligence
    vi = VisualIntelligence()
    assert vi is not None
    
    # Autonomous Agent
    agent = AutonomousAgent()
    plan = agent.create_plan("test task")
    assert plan is not None
    
    # Natural Language Tests
    generator = NaturalLanguageTestGenerator()
    test_case = generator.parse_natural_language("Test: Click button")
    assert test_case is not None
    
    print("✅ All features are working!")


if __name__ == "__main__":
    # Run basic smoke test
    test_all_features()
    
    # Run full test suite
    pytest.main([__file__, "-v"])