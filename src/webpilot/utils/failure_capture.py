#!/usr/bin/env python3
"""
Automatic failure capture utilities.

Provides screenshot, video, and diagnostic information on test failures.
"""

import os
import json
import time
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable
import logging
import functools

logger = logging.getLogger(__name__)


class FailureCapture:
    """
    Automatic failure capture configuration and handler.
    
    Example:
        pilot.config.failure_capture = FailureCapture(
            screenshot=True,
            video=True,
            html=True,
            console_logs=True,
            network_logs=True,
            directory="./test-failures"
        )
    """
    
    def __init__(
        self,
        screenshot: bool = True,
        video: bool = False,
        html: bool = True,
        console_logs: bool = True,
        network_logs: bool = True,
        performance_metrics: bool = True,
        directory: str = "./test-failures",
        on_failure: Optional[Callable] = None
    ):
        self.screenshot = screenshot
        self.video = video
        self.html = html
        self.console_logs = console_logs
        self.network_logs = network_logs
        self.performance_metrics = performance_metrics
        self.directory = Path(directory)
        self.on_failure = on_failure
        
        # Create directory if it doesn't exist
        self.directory.mkdir(parents=True, exist_ok=True)
        
    def capture_failure(self, pilot: Any, test_name: str, exception: Exception) -> Dict[str, Any]:
        """
        Capture all diagnostic information on failure.
        
        Args:
            pilot: WebPilot instance
            test_name: Name of the failed test
            exception: The exception that was raised
            
        Returns:
            Dictionary with paths to captured artifacts
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_dir = self.directory / f"{test_name}_{timestamp}"
        test_dir.mkdir(parents=True, exist_ok=True)
        
        artifacts = {
            "test_name": test_name,
            "timestamp": timestamp,
            "exception": str(exception),
            "traceback": traceback.format_exc(),
            "directory": str(test_dir)
        }
        
        try:
            # Capture screenshot
            if self.screenshot and hasattr(pilot, 'screenshot'):
                screenshot_path = test_dir / "screenshot.png"
                pilot.screenshot(str(screenshot_path))
                artifacts["screenshot"] = str(screenshot_path)
                logger.info(f"Screenshot saved to {screenshot_path}")
            
            # Capture HTML
            if self.html and hasattr(pilot, 'get_page_source'):
                html_path = test_dir / "page.html"
                html_content = pilot.get_page_source()
                html_path.write_text(html_content)
                artifacts["html"] = str(html_path)
                logger.info(f"HTML saved to {html_path}")
            
            # Capture console logs
            if self.console_logs and hasattr(pilot, 'get_console_logs'):
                console_path = test_dir / "console.json"
                console_logs = pilot.get_console_logs()
                console_path.write_text(json.dumps(console_logs, indent=2))
                artifacts["console_logs"] = str(console_path)
                logger.info(f"Console logs saved to {console_path}")
            
            # Capture network logs
            if self.network_logs and hasattr(pilot, 'get_network_logs'):
                network_path = test_dir / "network.json"
                network_logs = pilot.get_network_logs()
                network_path.write_text(json.dumps(network_logs, indent=2))
                artifacts["network_logs"] = str(network_path)
                logger.info(f"Network logs saved to {network_path}")
            
            # Capture performance metrics
            if self.performance_metrics and hasattr(pilot, 'get_performance_metrics'):
                perf_path = test_dir / "performance.json"
                perf_metrics = pilot.get_performance_metrics()
                perf_path.write_text(json.dumps(perf_metrics, indent=2))
                artifacts["performance_metrics"] = str(perf_path)
                logger.info(f"Performance metrics saved to {perf_path}")
            
            # Capture current URL
            if hasattr(pilot, 'current_url'):
                artifacts["url"] = pilot.current_url
            
            # Capture browser info
            if hasattr(pilot, 'get_browser_info'):
                artifacts["browser_info"] = pilot.get_browser_info()
            
            # Save summary
            summary_path = test_dir / "summary.json"
            summary_path.write_text(json.dumps(artifacts, indent=2))
            logger.info(f"Failure summary saved to {summary_path}")
            
            # Call custom failure handler if provided
            if self.on_failure:
                self.on_failure(pilot, artifacts)
            
        except Exception as e:
            logger.error(f"Error capturing failure artifacts: {e}")
            artifacts["capture_error"] = str(e)
        
        return artifacts


def capture_on_failure(capture_config: Optional[FailureCapture] = None):
    """
    Decorator to automatically capture failure information.
    
    Args:
        capture_config: FailureCapture configuration (uses default if None)
        
    Example:
        @capture_on_failure()
        def test_login(pilot):
            pilot.navigate("https://example.com")
            pilot.click("#login")  # May fail
    """
    if capture_config is None:
        capture_config = FailureCapture()
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Try to find pilot instance in args
            pilot = None
            for arg in args:
                if hasattr(arg, 'screenshot'):  # Duck typing for WebPilot
                    pilot = arg
                    break
            
            # Also check kwargs
            if pilot is None:
                pilot = kwargs.get('pilot')
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if pilot:
                    test_name = func.__name__
                    artifacts = capture_config.capture_failure(pilot, test_name, e)
                    logger.error(f"Test '{test_name}' failed. Artifacts saved to: {artifacts['directory']}")
                    
                    # Enhance exception with artifact information
                    e.failure_artifacts = artifacts
                raise
                
        return wrapper
    return decorator


class SmartErrorAnalyzer:
    """
    Provides intelligent error analysis and suggestions.
    """
    
    @staticmethod
    def analyze_element_not_found(selector: str, pilot: Any) -> Dict[str, Any]:
        """
        Analyze why an element was not found and provide suggestions.
        
        Returns:
            Dictionary with analysis and suggestions
        """
        analysis = {
            "selector": selector,
            "suggestions": [],
            "similar_elements": [],
            "possible_issues": []
        }
        
        # Check if selector syntax is valid
        if selector.startswith('#'):
            analysis["selector_type"] = "id"
            # Look for similar IDs
            if hasattr(pilot, 'find_elements_by_partial_id'):
                partial = selector[1:5] if len(selector) > 5 else selector[1:]
                similar = pilot.find_elements_by_partial_id(partial)
                if similar:
                    analysis["similar_elements"] = [elem.get_attribute('id') for elem in similar[:5]]
                    analysis["suggestions"].append(f"Did you mean one of these IDs? {analysis['similar_elements']}")
        
        elif selector.startswith('.'):
            analysis["selector_type"] = "class"
            # Look for similar classes
            if hasattr(pilot, 'find_elements_by_partial_class'):
                partial = selector[1:5] if len(selector) > 5 else selector[1:]
                similar = pilot.find_elements_by_partial_class(partial)
                if similar:
                    analysis["similar_elements"] = [elem.get_attribute('class') for elem in similar[:5]]
                    analysis["suggestions"].append(f"Did you mean one of these classes? {analysis['similar_elements']}")
        
        # Check common issues
        analysis["possible_issues"] = [
            "Element might be inside an iframe - use pilot.switch_to_iframe()",
            "Element might not be loaded yet - use pilot.wait_for_element()",
            "Element might be hidden - check display:none or visibility:hidden",
            "Selector syntax might be incorrect",
            "Element might be dynamically generated - wait for it to appear"
        ]
        
        # Check current page state
        if hasattr(pilot, 'current_url'):
            analysis["current_url"] = pilot.current_url
            analysis["suggestions"].append(f"Verify you're on the correct page: {pilot.current_url}")
        
        # Check if page is loaded
        if hasattr(pilot, 'is_page_loaded'):
            if not pilot.is_page_loaded():
                analysis["suggestions"].append("Page is still loading - add a wait")
        
        return analysis
    
    @staticmethod
    def generate_fix_suggestion(exception: Exception, pilot: Any) -> str:
        """
        Generate a suggested fix for the exception.
        
        Args:
            exception: The exception that occurred
            pilot: WebPilot instance
            
        Returns:
            String with suggested fix code
        """
        if "element not found" in str(exception).lower():
            return """
# Suggested fixes:

# 1. Wait for element to appear:
pilot.wait_for_element("#element", timeout=10)

# 2. Check if element is in iframe:
pilot.switch_to_iframe("iframe_name")
pilot.click("#element")
pilot.switch_to_default()

# 3. Use more robust selector:
pilot.click(text="Click me")  # Use text instead of selector

# 4. Add retry logic:
from webpilot.utils.retry import retry

@retry(times=3, delay=1)
def click_element():
    pilot.click("#element")
"""
        
        elif "timeout" in str(exception).lower():
            return """
# Suggested fixes:

# 1. Increase timeout:
pilot.wait_for_element("#element", timeout=30)

# 2. Wait for specific condition:
pilot.wait_for(lambda: pilot.is_element_visible("#element"))

# 3. Check network activity:
pilot.wait_for_network_idle(timeout=10)
"""
        
        else:
            return f"# No specific suggestion for: {exception}"