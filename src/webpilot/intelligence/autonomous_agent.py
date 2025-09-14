"""
Autonomous Agent for WebPilot

Self-healing, goal-oriented web automation that adapts and recovers from failures.
"""

import json
import time
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from ..core import WebPilot, ActionResult
from .visual_intelligence import VisualWebPilot
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class TaskStatus(Enum):
    """Status of a task execution."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RECOVERED = "recovered"
    ABANDONED = "abandoned"


@dataclass
class TaskStep:
    """Represents a single step in a task."""
    action: str
    arguments: Dict[str, Any]
    description: str
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[ActionResult] = None
    error: Optional[str] = None
    recovery_attempts: int = 0
    alternatives: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class TaskPlan:
    """Execution plan for a task."""
    goal: str
    steps: List[TaskStep]
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    success_rate: float = 0.0
    total_recoveries: int = 0


class RecoveryStrategy(Enum):
    """Recovery strategies for failed actions."""
    RETRY = "retry"  # Simple retry
    WAIT_RETRY = "wait_retry"  # Wait then retry
    ALTERNATIVE_SELECTOR = "alternative_selector"  # Try different selector
    VISUAL_FALLBACK = "visual_fallback"  # Use visual recognition
    REFRESH_RETRY = "refresh_retry"  # Refresh page and retry
    NAVIGATE_RETRY = "navigate_retry"  # Re-navigate and retry
    SKIP = "skip"  # Skip this step
    ABORT = "abort"  # Abort entire task


class AutonomousAgent:
    """
    Autonomous web automation agent with self-healing capabilities.
    
    Features:
    - Goal-oriented task planning
    - Automatic error recovery
    - Learning from failures
    - Alternative strategy generation
    - Visual fallback for failed selectors
    """
    
    def __init__(
        self,
        pilot: Optional[WebPilot] = None,
        max_recovery_attempts: int = 3,
        enable_visual_fallback: bool = True,
        enable_learning: bool = True
    ):
        """
        Initialize autonomous agent.
        
        Args:
            pilot: WebPilot instance to use
            max_recovery_attempts: Maximum recovery attempts per step
            enable_visual_fallback: Use visual recognition as fallback
            enable_learning: Learn from successes and failures
        """
        self.pilot = VisualWebPilot() if enable_visual_fallback else (pilot or WebPilot())
        self.max_recovery_attempts = max_recovery_attempts
        self.enable_visual_fallback = enable_visual_fallback
        self.enable_learning = enable_learning
        self.logger = get_logger(__name__)
        
        # Learning data
        self.success_patterns: Dict[str, List[Dict]] = {}
        self.failure_patterns: Dict[str, List[Dict]] = {}
        self.recovery_strategies: Dict[str, RecoveryStrategy] = {}
        
    def create_plan(self, goal: str, context: Optional[Dict[str, Any]] = None) -> TaskPlan:
        """
        Create execution plan for a goal.
        
        Args:
            goal: Natural language goal
            context: Optional context about current state
            
        Returns:
            Task execution plan
        """
        steps = self._decompose_goal(goal, context)
        return TaskPlan(goal=goal, steps=steps)
        
    def _decompose_goal(self, goal: str, context: Optional[Dict[str, Any]] = None) -> List[TaskStep]:
        """
        Decompose goal into executable steps.
        
        Args:
            goal: Natural language goal
            context: Current context
            
        Returns:
            List of task steps
        """
        steps = []
        goal_lower = goal.lower()
        
        # Common task patterns
        if "login" in goal_lower:
            steps.extend(self._create_login_steps(goal, context))
        elif "search" in goal_lower:
            steps.extend(self._create_search_steps(goal, context))
        elif "fill form" in goal_lower or "submit form" in goal_lower:
            steps.extend(self._create_form_steps(goal, context))
        elif "extract" in goal_lower or "scrape" in goal_lower:
            steps.extend(self._create_extraction_steps(goal, context))
        elif "navigate" in goal_lower or "go to" in goal_lower:
            steps.extend(self._create_navigation_steps(goal, context))
        else:
            # Generic steps for unknown goals
            steps.append(TaskStep(
                action="analyze",
                arguments={},
                description="Analyze current page"
            ))
            
        return steps
        
    def _create_login_steps(self, goal: str, context: Optional[Dict[str, Any]]) -> List[TaskStep]:
        """Create login task steps."""
        steps = []
        
        # Extract credentials from context or goal
        username = context.get('username') if context else None
        password = context.get('password') if context else None
        
        steps.append(TaskStep(
            action="find_element",
            arguments={"selector": "input[type='email'], input[type='text'], #username, #email"},
            description="Find username field",
            alternatives=[
                {"action": "visual_find", "arguments": {"description": "username or email field"}},
                {"action": "find_element", "arguments": {"selector": "input[name*='user']"}}
            ]
        ))
        
        if username:
            steps.append(TaskStep(
                action="type",
                arguments={"text": username},
                description="Enter username"
            ))
            
        steps.append(TaskStep(
            action="find_element",
            arguments={"selector": "input[type='password'], #password"},
            description="Find password field",
            alternatives=[
                {"action": "visual_find", "arguments": {"description": "password field"}}
            ]
        ))
        
        if password:
            steps.append(TaskStep(
                action="type",
                arguments={"text": password},
                description="Enter password"
            ))
            
        steps.append(TaskStep(
            action="click",
            arguments={"selector": "button[type='submit'], input[type='submit'], button:contains('Login')"},
            description="Click login button",
            alternatives=[
                {"action": "visual_click", "arguments": {"description": "login or submit button"}},
                {"action": "press_key", "arguments": {"key": "Enter"}}
            ]
        ))
        
        steps.append(TaskStep(
            action="wait",
            arguments={"seconds": 2},
            description="Wait for login to complete"
        ))
        
        return steps
        
    def _create_search_steps(self, goal: str, context: Optional[Dict[str, Any]]) -> List[TaskStep]:
        """Create search task steps."""
        import re
        
        steps = []
        
        # Extract search query
        query_match = re.search(r'search for["\s]+([^"]+)', goal, re.IGNORECASE)
        query = query_match.group(1) if query_match else context.get('query', '') if context else ''
        
        steps.append(TaskStep(
            action="find_element",
            arguments={"selector": "input[type='search'], input[type='text'], input[name*='search'], #search"},
            description="Find search field",
            alternatives=[
                {"action": "visual_find", "arguments": {"description": "search box or field"}}
            ]
        ))
        
        if query:
            steps.append(TaskStep(
                action="type",
                arguments={"text": query, "clear_first": True},
                description=f"Enter search query: {query}"
            ))
            
        steps.append(TaskStep(
            action="submit_search",
            arguments={},
            description="Submit search",
            alternatives=[
                {"action": "press_key", "arguments": {"key": "Enter"}},
                {"action": "click", "arguments": {"selector": "button[type='submit']"}},
                {"action": "visual_click", "arguments": {"description": "search button"}}
            ]
        ))
        
        steps.append(TaskStep(
            action="wait",
            arguments={"seconds": 2},
            description="Wait for results"
        ))
        
        return steps
        
    def _create_form_steps(self, goal: str, context: Optional[Dict[str, Any]]) -> List[TaskStep]:
        """Create form filling steps."""
        steps = []
        
        steps.append(TaskStep(
            action="analyze_form",
            arguments={},
            description="Analyze form structure"
        ))
        
        # Add form data from context
        if context and 'form_data' in context:
            for field, value in context['form_data'].items():
                steps.append(TaskStep(
                    action="fill_field",
                    arguments={"field": field, "value": value},
                    description=f"Fill {field} field"
                ))
                
        steps.append(TaskStep(
            action="submit_form",
            arguments={},
            description="Submit form",
            alternatives=[
                {"action": "click", "arguments": {"selector": "button[type='submit']"}},
                {"action": "visual_click", "arguments": {"description": "submit button"}}
            ]
        ))
        
        return steps
        
    def _create_extraction_steps(self, goal: str, context: Optional[Dict[str, Any]]) -> List[TaskStep]:
        """Create data extraction steps."""
        steps = []
        
        steps.append(TaskStep(
            action="wait_for_content",
            arguments={"timeout": 5},
            description="Wait for content to load"
        ))
        
        steps.append(TaskStep(
            action="extract",
            arguments={"format": "structured"},
            description="Extract page data"
        ))
        
        if "table" in goal.lower():
            steps.append(TaskStep(
                action="extract_tables",
                arguments={},
                description="Extract table data"
            ))
            
        if "links" in goal.lower():
            steps.append(TaskStep(
                action="extract_links",
                arguments={},
                description="Extract all links"
            ))
            
        return steps
        
    def _create_navigation_steps(self, goal: str, context: Optional[Dict[str, Any]]) -> List[TaskStep]:
        """Create navigation steps."""
        import re
        
        steps = []
        
        # Extract URL if present
        url_match = re.search(r'https?://[^\s]+', goal)
        if url_match:
            steps.append(TaskStep(
                action="navigate",
                arguments={"url": url_match.group()},
                description=f"Navigate to {url_match.group()}"
            ))
        else:
            # Try to extract navigation target
            nav_match = re.search(r'go to\s+([^,\.]+)', goal, re.IGNORECASE)
            if nav_match:
                target = nav_match.group(1).strip()
                steps.append(TaskStep(
                    action="click",
                    arguments={"text": target},
                    description=f"Navigate to {target}",
                    alternatives=[
                        {"action": "visual_click", "arguments": {"description": target}}
                    ]
                ))
                
        return steps
        
    async def execute_plan(
        self,
        plan: TaskPlan,
        progress_callback: Optional[Callable[[TaskStep], None]] = None
    ) -> TaskPlan:
        """
        Execute a task plan with self-healing.
        
        Args:
            plan: Task plan to execute
            progress_callback: Optional callback for progress updates
            
        Returns:
            Completed task plan with results
        """
        self.logger.info(f"Executing plan for goal: {plan.goal}")
        
        for step in plan.steps:
            step.status = TaskStatus.IN_PROGRESS
            
            if progress_callback:
                progress_callback(step)
                
            # Execute step with recovery
            success = await self._execute_step_with_recovery(step)
            
            if success:
                step.status = TaskStatus.COMPLETED
            else:
                step.status = TaskStatus.FAILED
                
                # Decide whether to continue
                if not self._should_continue_after_failure(step, plan):
                    break
                    
        # Calculate success rate
        completed = sum(1 for s in plan.steps if s.status == TaskStatus.COMPLETED)
        plan.success_rate = completed / len(plan.steps) if plan.steps else 0
        plan.completed_at = datetime.now()
        
        # Learn from execution
        if self.enable_learning:
            self._learn_from_execution(plan)
            
        return plan
        
    async def _execute_step_with_recovery(self, step: TaskStep) -> bool:
        """
        Execute a step with automatic recovery.
        
        Args:
            step: Step to execute
            
        Returns:
            True if step succeeded (possibly after recovery)
        """
        attempt = 0
        
        while attempt <= self.max_recovery_attempts:
            try:
                # Execute the action
                result = await self._execute_action(step.action, step.arguments)
                
                if result.success:
                    step.result = result
                    if attempt > 0:
                        step.status = TaskStatus.RECOVERED
                        self.logger.info(f"Step recovered after {attempt} attempts")
                    return True
                else:
                    step.error = result.error
                    
                    if attempt < self.max_recovery_attempts:
                        # Try recovery
                        recovery_strategy = self._determine_recovery_strategy(step, result)
                        
                        if recovery_strategy == RecoveryStrategy.ABORT:
                            break
                            
                        await self._apply_recovery_strategy(step, recovery_strategy)
                        attempt += 1
                        step.recovery_attempts = attempt
                    else:
                        # Try alternatives if available
                        if step.alternatives and attempt == self.max_recovery_attempts:
                            for alt in step.alternatives:
                                alt_result = await self._execute_action(
                                    alt['action'],
                                    alt['arguments']
                                )
                                if alt_result.success:
                                    step.result = alt_result
                                    step.status = TaskStatus.RECOVERED
                                    self.logger.info(f"Step succeeded with alternative: {alt}")
                                    return True
                        break
                        
            except Exception as e:
                self.logger.error(f"Unexpected error in step: {e}")
                step.error = str(e)
                attempt += 1
                
        return False
        
    async def _execute_action(self, action: str, arguments: Dict[str, Any]) -> ActionResult:
        """
        Execute a single action.
        
        Args:
            action: Action to execute
            arguments: Action arguments
            
        Returns:
            Action result
        """
        # Map actions to pilot methods
        if action == "navigate":
            return self.pilot.navigate(arguments['url'])
        elif action == "click":
            return self.pilot.click(**arguments)
        elif action == "type":
            return self.pilot.type_text(**arguments)
        elif action == "find_element":
            # Check if element exists
            elements = self.pilot.find_elements(arguments.get('selector'))
            return ActionResult(
                success=len(elements) > 0,
                data=elements,
                error="Element not found" if not elements else None
            )
        elif action == "visual_find" and self.enable_visual_fallback:
            # Use visual intelligence
            analysis = self.pilot.visual.capture_and_analyze()
            element = self.pilot.visual._find_element_by_description(arguments['description'])
            return ActionResult(
                success=element is not None,
                data=element,
                error=f"Could not find: {arguments['description']}" if not element else None
            )
        elif action == "visual_click" and self.enable_visual_fallback:
            return self.pilot.visual_click(arguments['description'])
        elif action == "wait":
            return self.pilot.wait(arguments['seconds'])
        elif action == "extract":
            return self.pilot.extract_page_content()
        elif action == "press_key":
            return self.pilot.press_key(arguments['key'])
        elif action == "submit_search" or action == "submit_form":
            # Try pressing Enter
            return self.pilot.press_key("Enter")
        elif action == "analyze_form":
            # Analyze form structure
            if self.enable_visual_fallback:
                analysis = self.pilot.visual.capture_and_analyze()
                return ActionResult(success=True, data=analysis.forms)
            else:
                return ActionResult(success=True, data={})
        elif action == "fill_field":
            # Fill a specific field
            selector = f"input[name='{arguments['field']}'], #{arguments['field']}"
            click_result = self.pilot.click(selector=selector)
            if click_result.success:
                return self.pilot.type_text(arguments['value'])
            return click_result
        elif action == "wait_for_content":
            return self.pilot.wait_for_element("body", timeout=arguments.get('timeout', 5))
        elif action == "extract_tables":
            return self.pilot.extract_tables()
        elif action == "extract_links":
            return self.pilot.extract_links()
        else:
            return ActionResult(success=False, error=f"Unknown action: {action}")
            
    def _determine_recovery_strategy(self, step: TaskStep, result: ActionResult) -> RecoveryStrategy:
        """
        Determine recovery strategy based on failure.
        
        Args:
            step: Failed step
            result: Failure result
            
        Returns:
            Recovery strategy to apply
        """
        error = result.error or ""
        
        # Check learned strategies first
        if step.action in self.recovery_strategies:
            return self.recovery_strategies[step.action]
            
        # Heuristic-based strategy selection
        if "not found" in error.lower() or "no such element" in error.lower():
            if self.enable_visual_fallback and step.recovery_attempts == 0:
                return RecoveryStrategy.VISUAL_FALLBACK
            elif step.recovery_attempts == 1:
                return RecoveryStrategy.WAIT_RETRY
            else:
                return RecoveryStrategy.ALTERNATIVE_SELECTOR
                
        elif "timeout" in error.lower():
            return RecoveryStrategy.WAIT_RETRY
            
        elif "stale" in error.lower():
            return RecoveryStrategy.REFRESH_RETRY
            
        elif step.recovery_attempts < 2:
            return RecoveryStrategy.RETRY
            
        else:
            return RecoveryStrategy.SKIP
            
    async def _apply_recovery_strategy(self, step: TaskStep, strategy: RecoveryStrategy):
        """
        Apply recovery strategy to a step.
        
        Args:
            step: Step to recover
            strategy: Recovery strategy to apply
        """
        self.logger.info(f"Applying recovery strategy: {strategy.value}")
        
        if strategy == RecoveryStrategy.RETRY:
            # Just retry - no changes needed
            pass
            
        elif strategy == RecoveryStrategy.WAIT_RETRY:
            # Wait before retry
            await self.pilot.wait(2)
            
        elif strategy == RecoveryStrategy.ALTERNATIVE_SELECTOR:
            # Modify selector to be more generic
            if 'selector' in step.arguments:
                original = step.arguments['selector']
                # Try more generic selector
                if '#' in original:
                    # ID selector - try by type
                    step.arguments['selector'] = f"input, button"
                elif '[' in original:
                    # Attribute selector - try by tag
                    tag = original.split('[')[0]
                    step.arguments['selector'] = tag or "*"
                    
        elif strategy == RecoveryStrategy.VISUAL_FALLBACK:
            # Switch to visual mode
            if self.enable_visual_fallback:
                step.action = f"visual_{step.action}"
                if 'selector' in step.arguments:
                    step.arguments['description'] = step.arguments.pop('selector')
                    
        elif strategy == RecoveryStrategy.REFRESH_RETRY:
            # Refresh page
            await self.pilot.refresh()
            await self.pilot.wait(2)
            
        elif strategy == RecoveryStrategy.NAVIGATE_RETRY:
            # Re-navigate to current URL
            current_url = self.pilot.get_current_url()
            if current_url:
                await self.pilot.navigate(current_url)
                await self.pilot.wait(2)
                
    def _should_continue_after_failure(self, failed_step: TaskStep, plan: TaskPlan) -> bool:
        """
        Decide whether to continue after step failure.
        
        Args:
            failed_step: Step that failed
            plan: Overall plan
            
        Returns:
            True if should continue
        """
        # Check if step is critical
        critical_actions = ['navigate', 'login', 'authenticate']
        if failed_step.action in critical_actions:
            return False
            
        # Check success rate so far
        completed = sum(1 for s in plan.steps if s.status == TaskStatus.COMPLETED)
        total_attempted = completed + sum(1 for s in plan.steps if s.status == TaskStatus.FAILED)
        
        if total_attempted > 0:
            success_rate = completed / total_attempted
            if success_rate < 0.3:  # Less than 30% success
                return False
                
        return True
        
    def _learn_from_execution(self, plan: TaskPlan):
        """
        Learn from plan execution.
        
        Args:
            plan: Completed plan
        """
        for step in plan.steps:
            if step.status == TaskStatus.COMPLETED:
                # Record success pattern
                pattern = {
                    'action': step.action,
                    'arguments': step.arguments,
                    'context': step.description
                }
                
                if step.action not in self.success_patterns:
                    self.success_patterns[step.action] = []
                self.success_patterns[step.action].append(pattern)
                
            elif step.status == TaskStatus.FAILED:
                # Record failure pattern
                pattern = {
                    'action': step.action,
                    'arguments': step.arguments,
                    'error': step.error,
                    'recovery_attempts': step.recovery_attempts
                }
                
                if step.action not in self.failure_patterns:
                    self.failure_patterns[step.action] = []
                self.failure_patterns[step.action].append(pattern)
                
            elif step.status == TaskStatus.RECOVERED:
                # Learn successful recovery strategy
                if step.recovery_attempts > 0:
                    # The last recovery strategy worked
                    self.recovery_strategies[step.action] = RecoveryStrategy.VISUAL_FALLBACK  # Example
                    
    def export_learning_data(self) -> Dict[str, Any]:
        """
        Export learned patterns and strategies.
        
        Returns:
            Learning data
        """
        return {
            'success_patterns': self.success_patterns,
            'failure_patterns': self.failure_patterns,
            'recovery_strategies': {
                k: v.value for k, v in self.recovery_strategies.items()
            }
        }
        
    def import_learning_data(self, data: Dict[str, Any]):
        """
        Import learned patterns and strategies.
        
        Args:
            data: Learning data to import
        """
        self.success_patterns = data.get('success_patterns', {})
        self.failure_patterns = data.get('failure_patterns', {})
        
        strategies = data.get('recovery_strategies', {})
        for action, strategy_str in strategies.items():
            try:
                self.recovery_strategies[action] = RecoveryStrategy(strategy_str)
            except ValueError:
                pass


class SmartAutomation:
    """
    High-level interface for autonomous web automation.
    
    Simplifies common automation tasks with self-healing capabilities.
    """
    
    def __init__(self, headless: bool = False):
        """Initialize smart automation."""
        self.pilot = VisualWebPilot(headless=headless)
        self.agent = AutonomousAgent(self.pilot)
        
    async def login(
        self,
        url: str,
        username: str,
        password: str,
        success_indicator: Optional[str] = None
    ) -> bool:
        """
        Smart login with automatic form detection and recovery.
        
        Args:
            url: Login page URL
            username: Username/email
            password: Password
            success_indicator: Element/text that indicates successful login
            
        Returns:
            True if login successful
        """
        # Navigate to login page
        self.pilot.start(url)
        
        # Create login plan
        plan = self.agent.create_plan(
            "login to website",
            context={'username': username, 'password': password}
        )
        
        # Execute with recovery
        completed_plan = await self.agent.execute_plan(plan)
        
        # Check success
        if success_indicator:
            # Look for success indicator
            if self.agent.enable_visual_fallback:
                analysis = self.pilot.visual.capture_and_analyze()
                for elem in analysis.elements:
                    if elem.text and success_indicator.lower() in elem.text.lower():
                        return True
            else:
                elements = self.pilot.find_elements(f"*:contains('{success_indicator}')")
                return len(elements) > 0
                
        return completed_plan.success_rate > 0.7
        
    async def search(
        self,
        query: str,
        results_selector: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Smart search with automatic search box detection.
        
        Args:
            query: Search query
            results_selector: Selector for results
            
        Returns:
            Search results
        """
        plan = self.agent.create_plan(
            f"search for {query}",
            context={'query': query}
        )
        
        completed_plan = await self.agent.execute_plan(plan)
        
        if completed_plan.success_rate > 0.5:
            # Extract results
            if results_selector:
                elements = self.pilot.find_elements(results_selector)
                return [{'text': elem.text, 'href': elem.get_attribute('href')} for elem in elements]
            else:
                # Extract all content
                result = self.pilot.extract_page_content()
                if result.success:
                    return [result.data]
                    
        return []
        
    async def fill_form(
        self,
        form_data: Dict[str, Any],
        submit: bool = True
    ) -> bool:
        """
        Smart form filling with field detection and validation.
        
        Args:
            form_data: Dictionary of field names/values
            submit: Whether to submit after filling
            
        Returns:
            True if form filled successfully
        """
        goal = "fill and submit form" if submit else "fill form"
        
        plan = self.agent.create_plan(
            goal,
            context={'form_data': form_data}
        )
        
        completed_plan = await self.agent.execute_plan(plan)
        
        return completed_plan.success_rate > 0.7
        
    async def extract_data(
        self,
        url: str,
        wait_for: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Smart data extraction with content detection.
        
        Args:
            url: Page URL
            wait_for: Element to wait for before extraction
            
        Returns:
            Extracted data
        """
        # Navigate
        self.pilot.start(url)
        
        if wait_for:
            self.pilot.wait_for_element(wait_for)
            
        # Create extraction plan
        plan = self.agent.create_plan("extract all data from page")
        
        completed_plan = await self.agent.execute_plan(plan)
        
        # Get results
        for step in completed_plan.steps:
            if step.action == "extract" and step.result and step.result.success:
                return step.result.data
                
        return {}
        
    def close(self):
        """Close browser and cleanup."""
        self.pilot.close()