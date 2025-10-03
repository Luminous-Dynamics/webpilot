"""
WebPilot v2.0 - AI Orchestration Layer
Natural language automation powered by LLMs
"""

from typing import Optional, Any, Dict, List, Union
from dataclasses import dataclass
import asyncio
import json
import time

from .playwright_adapter import PlaywrightAdapter
from ..ai.llm_client import LLMClient
from ..ai.natural_language import NaturalLanguageProcessor
from ..ai.smart_assertions import SmartAssertions
from ..ai.page_analyzer import PageAnalyzer
from ..ai.test_generator import TestGenerator


@dataclass
class WebPilotConfig:
    """Configuration for AIWebPilot."""
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    api_key: Optional[str] = None
    auto_heal: bool = True
    verbose: bool = False
    learning_enabled: bool = False
    temperature: float = 0.7
    max_retries: int = 3
    timeout: int = 30000


class AIWebPilot:
    """
    The AI orchestration layer for Playwright.
    Enables natural language test automation.
    """
    
    def __init__(
        self, 
        page: Any,  # Playwright page object
        config: Optional[WebPilotConfig] = None,
        **kwargs
    ):
        """
        Initialize AIWebPilot with Playwright page and configuration.
        
        Args:
            page: Playwright page object (sync or async)
            config: WebPilot configuration
            **kwargs: Override config values
        """
        # Initialize configuration
        self.config = config or WebPilotConfig()
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        # Initialize adapter
        self.adapter = PlaywrightAdapter(page)
        
        # Initialize AI components
        self.llm_client = LLMClient(
            provider=self.config.llm_provider,
            model=self.config.llm_model,
            api_key=self.config.api_key,
            temperature=self.config.temperature
        )
        
        self.nl_processor = NaturalLanguageProcessor(self.llm_client)
        self.smart_assertions = SmartAssertions(self.llm_client, self.adapter)
        self.page_analyzer = PageAnalyzer(self.llm_client, self.adapter)
        self.test_generator = TestGenerator(self.llm_client)
        
        # Interaction memory for learning
        self.interaction_history: List[Dict] = []
        
    async def execute(self, instruction: str, **context) -> Any:
        """
        Execute a natural language instruction.
        
        Args:
            instruction: Natural language command
            **context: Additional context for execution
            
        Returns:
            Result of the execution
        
        Examples:
            await pilot.execute("Go to google.com")
            await pilot.execute("Search for WebPilot")
            await pilot.execute("Click the first result")
        """
        start_time = time.time()
        
        if self.config.verbose:
            print(f"🤖 Processing: {instruction}")
        
        try:
            # Parse natural language to intent
            intent = await self.nl_processor.parse_intent(instruction)
            
            if self.config.verbose:
                print(f"📋 Intent: {intent}")
            
            # Get current page context
            page_context = await self._get_page_context()
            
            # Plan actions based on intent and context
            actions = await self.nl_processor.plan_actions(
                intent, 
                {**page_context, **context}
            )
            
            if self.config.verbose:
                print(f"📝 Actions: {actions}")
            
            # Execute actions
            results = []
            for action in actions:
                result = await self._execute_action(action)
                results.append(result)
            
            # Record interaction for learning
            if self.config.learning_enabled:
                self._record_interaction(instruction, intent, actions, results)
            
            execution_time = time.time() - start_time
            
            if self.config.verbose:
                print(f"✅ Completed in {execution_time:.2f}s")
            
            return results[-1] if results else None
            
        except Exception as e:
            if self.config.auto_heal:
                return await self._heal_and_retry(instruction, e, context)
            raise
    
    async def _execute_action(self, action: Dict) -> Any:
        """
        Execute a single action.
        
        Args:
            action: Action dictionary with 'type' and 'params'
            
        Returns:
            Result of the action
        """
        action_type = action.get('type')
        params = action.get('params', {})
        
        # Map high-level actions to Playwright methods
        action_mapping = {
            'navigate': 'goto',
            'click': 'click',
            'type': 'fill',
            'select': 'select_option',
            'wait': 'wait_for_selector',
            'screenshot': 'screenshot',
            'scroll': 'evaluate',
        }
        
        playwright_action = action_mapping.get(action_type, action_type)
        
        # Special handling for some actions
        if action_type == 'scroll':
            params = {'expression': f"window.scrollTo(0, {params.get('y', 'document.body.scrollHeight')})"}
            return await self.adapter.evaluate_javascript(params['expression'])
        
        # Execute via adapter
        return await self.adapter.execute_playwright_action(playwright_action, **params)
    
    async def _get_page_context(self) -> Dict:
        """Get current page context for AI decision making."""
        return {
            'url': self.adapter.get_url(),
            'title': self.adapter.get_title(),
            'timestamp': time.time(),
        }
    
    async def _heal_and_retry(self, instruction: str, error: Exception, context: Dict) -> Any:
        """
        Attempt to heal from an error and retry.
        
        Args:
            instruction: Original instruction
            error: The error that occurred
            context: Execution context
            
        Returns:
            Result after healing
        """
        if self.config.verbose:
            print(f"🔧 Auto-healing: {error}")
        
        # Analyze the error and page state
        page_content = await self.adapter.get_page_content()
        
        # Ask AI to suggest alternative approach
        healing_prompt = f"""
        Failed to execute: {instruction}
        Error: {error}
        Page URL: {self.adapter.get_url()}
        
        Suggest an alternative approach to achieve the same goal.
        """
        
        alternative = await self.llm_client.complete(healing_prompt)
        
        # Try the alternative approach
        return await self.execute(alternative, **context)
    
    def _record_interaction(self, instruction: str, intent: Dict, actions: List, results: List):
        """Record interaction for learning and improvement."""
        self.interaction_history.append({
            'instruction': instruction,
            'intent': intent,
            'actions': actions,
            'results': results,
            'timestamp': time.time(),
            'success': all(r is not None for r in results)
        })
    
    async def assert_visual(self, assertion: str) -> bool:
        """
        Perform a visual assertion using natural language.
        
        Args:
            assertion: Natural language assertion
            
        Returns:
            True if assertion passes
            
        Examples:
            await pilot.assert_visual("The login button should be blue")
            await pilot.assert_visual("Error message is visible")
        """
        return await self.smart_assertions.assert_visual(assertion)
    
    async def explain_page(self) -> str:
        """
        Get an AI explanation of the current page.
        
        Returns:
            Natural language description of the page
        """
        return await self.page_analyzer.explain_page()
    
    async def find_element(self, description: str) -> Optional[str]:
        """
        Find an element using natural language description.
        
        Args:
            description: Natural language element description
            
        Returns:
            Selector for the element, or None if not found
            
        Examples:
            await pilot.find_element("the big blue submit button")
            await pilot.find_element("search box at the top")
        """
        return await self.page_analyzer.find_element_by_description(description)
    
    async def generate_test(self, user_story: str) -> str:
        """
        Generate a test from a user story.
        
        Args:
            user_story: Natural language user story
            
        Returns:
            Generated test code
        """
        return await self.test_generator.generate_from_user_story(user_story)
    
    async def suggest_improvements(self) -> List[str]:
        """
        Suggest test improvements based on interaction history.
        
        Returns:
            List of improvement suggestions
        """
        if not self.interaction_history:
            return ["No interactions recorded yet"]
        
        # Analyze patterns in history
        failed_interactions = [i for i in self.interaction_history if not i['success']]
        
        suggestions = []
        
        if failed_interactions:
            suggestions.append(f"Consider adding error handling for {len(failed_interactions)} failed interactions")
        
        # More sophisticated analysis could go here
        
        return suggestions